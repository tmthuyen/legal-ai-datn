import json
import os
import time

import torch
from transformers import (
    StoppingCriteria,
    StoppingCriteriaList,
)

from src.common.custom_exception import CustomException
from src.models.base_model import BaseLegalModel, Prompt
from src.utils.logger import setup_logger

logger = setup_logger("legal_model", "legal_model.log")

# load model util


class MultiTaskStoppingCriteria(StoppingCriteria):
    """Stopping criteria tổng quát cho nhiều định dạng output khác nhau (JSON, List, Boolean, Text)."""

    def __init__(self, tokenizer, prompt_length: int, output_type: str):
        """Khởi tạo cơ chế dừng

        Args:
            tokenizer (_type_): _tokenizer của mô hình
            prompt_length (int): độ dài của prompt (số lượng token) để xác định phần text sinh ra từ mô hình
            output_type (str): loại output mong muốn: "json", "list", "boolean", "str"
        """
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length
        self.output_type = output_type

    def __call__(self, input_ids, scores, **kwargs) -> torch.Tensor:
        # Lấy phần text model vừa sinh ra đến thời điểm hiện tại
        generated_text = self.tokenizer.decode(
            input_ids[0, self.prompt_length :], skip_special_tokens=True
        )

        is_complete = False

        if self.output_type == "json":
            # Kiểm tra object JSON hoàn chỉnh {...}
            start = generated_text.find("{")
            if start != -1:
                try:
                    json.JSONDecoder().raw_decode(generated_text[start:])
                    is_complete = True
                except json.JSONDecodeError:
                    pass

        elif self.output_type == "list":
            # Kiểm tra mảng JSON hoàn chỉnh [...]
            start = generated_text.find("[")
            if start != -1:
                try:
                    json.JSONDecoder().raw_decode(generated_text[start:])
                    is_complete = True
                except json.JSONDecodeError:
                    pass

        elif self.output_type == "boolean":
            # Dừng ngay khi sinh xong từ khóa True/False hoặc có/không
            cleaned = generated_text.strip().lower()
            if any(
                val in cleaned
                for val in [
                    "true",
                    "false",
                    "False",
                    "True",
                    "đúng",
                    "sai",
                    "có",
                    "không",
                ]
            ):
                is_complete = True

        return torch.tensor([is_complete], dtype=torch.bool, device=input_ids.device)


class LegalReasoningModel(BaseLegalModel):
    def __init__(
        self,
        base_model_name: str,
        model_id: str,
        revision: str,
        tasks: dict | None = None,
    ):
        super().__init__(
            base_model_name=base_model_name, model_id=model_id, revision=revision
        )
        if tasks:
            self.tasks.update(tasks)

        self.tasks = {
            "LEGAL_QUERY_REFERENCE_HIERARCHY_EXTRACTION": {
                "prompt": Prompt.LEGAL_QRHE_PROMPT,
                "required_keys": [
                    "document",
                    "part",
                    "chapter",
                    "section",
                    "subsection",
                    "article",
                    "clause",
                    "point",
                ],
                "output_type": "json",  # json, list, str, boolean
                "max_new_tokens": 128,
            }
        }

        logger.info(f"Tasks đã đăng ký: {list(self.tasks.keys())}")

    @torch.inference_mode()
    def predict(self, task_id: str, input_text: str) -> dict:
        """Dự đoán từ mô hình

        Args:
            task_id (str): ID của task đã được đăng ký
            input_text (str): Truy vấn đầu vào để model thực hiện task

        Raises:
            CustomException: Nếu task_id chưa được đăng ký trong self.tasks

        Returns:
            dict: Kết quả dự đoán từ mô hình, bao gồm task_id, success, message, status_code, và result (raw_output và output)
            {
                "task_id": task_id,
                "success": True/False,
                "message": "Thông báo kết quả",
                "status_code": 200/500,
                "result": {
                    "raw_output": "Kết quả thô từ mô hình",
                    "output": "Kết quả đã được xử lý (JSON hoặc chuỗi)"
                }
            }
        """
        logger.info(
            f"Bắt đầu dự đoán cho task_id: {task_id} với input_text: '{input_text}'"
        )
        start_time = time.time()

        task = self.tasks.get(task_id)
        if task is None:
            raise CustomException(
                message=f"Task chưa được đăng ký: {task_id}", status_code=500
            )

        output_type = task.get("output_type", "json")
        max_new_tokens = task.get("max_new_tokens", 128)

        messages = self.build_messages(task_id, input_text)

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(self.device)

        # Tính toán độ dài prompt để xác định phần text sinh ra từ mô hình
        prompt_length = inputs["input_ids"].shape[-1]
        logger.info(f"Độ dài prompt: {prompt_length} token")

        # Qwen dùng <|im_end|> để kết thúc một lượt hội thoại
        im_end_id = self.tokenizer.convert_tokens_to_ids("<|im_end|>")

        stop_ids = [self.tokenizer.eos_token_id]
        if im_end_id is not None and im_end_id not in stop_ids:
            stop_ids.append(im_end_id)

        # Cơ chế dùng sunh
        stopping_criteria = None
        if output_type in ["json", "list", "boolean"]:
            stopping_criteria = StoppingCriteriaList(
                [
                    MultiTaskStoppingCriteria(
                        tokenizer=self.tokenizer,
                        prompt_length=prompt_length,
                        output_type=output_type,
                    )
                ]
            )

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            eos_token_id=stop_ids,
            pad_token_id=(
                self.tokenizer.pad_token_id
                if self.tokenizer.pad_token_id is not None
                else self.tokenizer.eos_token_id
            ),
            stopping_criteria=stopping_criteria,  # Cơ chế dừng sinh output khi sinh đủ thông tin cần thiết
            # repetition_penalty=1.05,
            # temperature=None,
            # top_p=None,
            # top_k=None,
        )

        input_length = inputs["input_ids"].shape[-1]
        generated_ids = outputs[0, input_length:]

        raw_output = self.tokenizer.decode(
            generated_ids, skip_special_tokens=True
        ).strip()

        parsed_output = self.parse_model_output(
            raw_output=raw_output, output_type=output_type
        )

        logger.info(f"Output thô từ model: {raw_output}")
        logger.info(f"Output đã được parse: {parsed_output}")
        logger.info(f"Output type yêu cầu: {output_type}")
        logger.info(f"Max new tokens: {max_new_tokens}")

        # Đo thời gian chạy của hàm predict và log vào file JSONL
        end_time = time.time()
        response_time_ms = round(
            (end_time - start_time) * 1000, 2
        )  # Tính thời gian chạy theo mili-giây

        # 2. Gọi hàm log ngay sau đó
        self.log_prediction_to_jsonl(
            input=input_text,
            response_time=response_time_ms,
            raw_output=raw_output,
            parsed_output=parsed_output,
            task_id=task_id,
            log_file_path="logs/extraction_prod.jsonl",
        )
        # ===================

        if task["output_type"] not in ["json", "list"]:
            logger.info(
                f"Output không yêu cầu là JSON hoặc List, trả về kết quả trực tiếp."
            )

            return {
                "task_id": task_id,
                "success": True,
                "message": "Thành công",
                "status_code": 200,
                "result": {
                    "raw_output": raw_output,
                    "output": parsed_output,
                },
            }

        if not isinstance(parsed_output, dict) and not isinstance(parsed_output, list):
            logger.error(f"Output không phải là một đối tượng JSON. Trả về None")
            return {
                "task_id": task_id,
                "success": False,
                "message": f"Output không phải là một đối tượng {output_type}. Trả về None.",
                "status_code": 500,
                "result": {
                    "raw_output": raw_output,
                    "output": None,
                },
            }

        if output_type == "json":
            required_keys = task["required_keys"]
            missing_keys = [key for key in required_keys if key not in parsed_output]

            if missing_keys:
                logger.error(
                    f"Output thiếu các trường bắt buộc: {', '.join(missing_keys)}"
                )
                return {
                    "task_id": task_id,
                    "success": False,
                    "message": f"Output thiếu các trường bắt buộc: {', '.join(missing_keys)}",
                    "status_code": 500,
                    "result": {
                        "raw_output": raw_output,
                        "output": None,
                    },
                }
        logger.info(f"Output hợp lệ, trả về kết quả.")

        return {
            "task_id": task_id,
            "success": True,
            "message": "Thành công",
            "status_code": 200,
            "result": {
                "raw_output": raw_output,
                "output": parsed_output,
            },
        }
