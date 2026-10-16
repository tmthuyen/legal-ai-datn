import json
import os
from abc import ABC, abstractmethod
from ast import parse
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    StoppingCriteria,
    StoppingCriteriaList,
)

from src.common.custom_exception import CustomException
from src.utils.logger import setup_logger

logger = setup_logger("legal_model", "legal_model.log")

# load model util

# Thư mục cache nằm ở root project, không phụ thuộc thư mục chạy lệnh
BACKEND_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = BACKEND_DIR / "models" / ".cache"


def get_model_snapshot(repo_id: str, revision: str = "main") -> str:
    logger.info(f"Thư mục cache cho model: {CACHE_DIR}")
    try:
        # Tải phiên bản mới nhất của revision nếu có kết nối mạng.
        # File đã có trong cache sẽ được tái sử dụng.
        path = snapshot_download(
            repo_id=repo_id,
            revision=revision,
            cache_dir=str(CACHE_DIR),
        )
        logger.info("Model snapshot: %s", path)
        return path

    except Exception:
        # Nếu mạng lỗi, thử dùng snapshot đã cache trước đó.
        logger.warning(
            "Không tải/kiểm tra được Hugging Face; thử dùng cache local.",
            exc_info=True,
        )
        return snapshot_download(
            repo_id=repo_id,
            revision=revision,
            cache_dir=str(CACHE_DIR),
            local_files_only=True,
        )


def load_model(
    base_model: str, adapter_model: str, revision: str = "main"
) -> tuple[AutoTokenizer, PeftModel]:
    base_path = get_model_snapshot(repo_id=base_model, revision=revision)
    adapter_path = get_model_snapshot(repo_id=adapter_model, revision=revision)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32

    tokenizer = AutoTokenizer.from_pretrained(
        base_path,
        local_files_only=True,
    )
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        base_path,
        # torch_dtype=dtype,
        dtype=dtype,
        local_files_only=True,
    )

    model = PeftModel.from_pretrained(
        base,
        adapter_path,
        is_trainable=False,
    )
    model.to(device)
    model.eval()
    model.config.use_cache = True

    logger.info("Legal AI model được tải thành công trên %s (%s)", device, dtype)

    return tokenizer, model


class Prompt:
    SYSTEM_PROMPT = """
    Bạn là model AI xử lý các nhiệm vụ pháp luật Việt Nam.
    Thực hiện đúng TASK được chỉ định trong đầu vào.
    Tuân thủ schema đầu ra của task đó.
    Không tự bịa thông tin hoặc căn cứ pháp luật.
    """

    # TASK: LEGAL_QUERY_REFERENCE_HIERARCHY_EXTRACTION
    LEGAL_QRHE_PROMPT = """
    TASK: LEGAL_QUERY_REFERENCE_HIERARCHY_EXTRACTION

    Nhiệm vụ:
    Trích xuất các cấp trích dẫn và văn bản pháp luật
    được đề cập rõ ràng trong input.

    Chỉ trả về JSON hợp lệ gồm các trường:
    document, part, chapter, section, subsection,
    article, clause, point.

    Cấp không được đề cập phải là null.
    Giá trị trích dẫn là chuỗi.
    Không suy đoán, bịa đặt hoặc bổ sung thông tin.
    Tuân thủ đúng schema đầu ra.
    """


class LegalModelTaskID:
    LEGAL_QUERY_REFERENCE_HIERARCHY_EXTRACTION = (
        "LEGAL_QUERY_REFERENCE_HIERARCHY_EXTRACTION"
    )


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


class BaseLegalModel(ABC):
    def __init__(
        self,
        base_model_name: str,
        model_id: str,
        revision: str = "main",
        tasks: dict | None = None,
    ):
        """Khởi tạo mô hình suy luận có trích dẫn Luật

        Args:
            base_model (str): tên mô hình cơ sở được sử dụng
            model_id (str): ID của mô hình đã fine tune
            tasks (dict | None, optional): danh sách các task đã được đăng ký. Defaults to None.
        """

        if not base_model_name or not model_id:
            raise CustomException(
                message="base_model và model_id là bắt buộc",
                status_code=500,
            )

        self.tokenizer, self.model = load_model(
            base_model=base_model_name, adapter_model=model_id, revision=revision
        )

        self.tasks = {}
        if tasks:
            self.tasks.update(tasks)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = torch.float16 if self.device.type == "cuda" else torch.float32

        logger.info(
            f"Khởi tạo mô hình {base_model_name} với adapter {model_id} thành công."
        )

    def parse_model_output(self, raw_output: str, output_type: str = "json"):
        """
        Parse chuỗi thô từ model dựa theo định dạng output_type yêu cầu của task.
        """
        cleaned_output = raw_output.strip()

        if output_type == "str":
            return cleaned_output

        if output_type == "boolean":
            lower_text = cleaned_output.lower()
            if any(val in lower_text for val in ["true", "đúng", "có"]):
                return True
            if any(val in lower_text for val in ["false", "sai", "không"]):
                return False
            return None

        if output_type in ["json", "list"]:
            target_char = "{" if output_type == "json" else "["
            end_char = "}" if output_type == "json" else "]"

            try:
                # Tìm vị trí bắt đầu và kết thúc của cấu trúc JSON/List
                start = cleaned_output.find(target_char)
                end = cleaned_output.rfind(end_char)

                if start != -1 and end != -1 and end > start:
                    json_str = cleaned_output[start : end + 1]
                    return json.loads(json_str)

                # Fallback dùng raw_decode nếu layout có chữ thừa ở đuôi
                decoder = json.JSONDecoder()
                if start != -1:
                    result, _ = decoder.raw_decode(cleaned_output[start:])
                    return result

            except (json.JSONDecodeError, ValueError):
                logger.error(
                    f"JSONDecodeError: Không thể parse output thành {output_type}. Trả về None"
                )
                pass

            return None

        return cleaned_output

    @abstractmethod
    def predict(self, task_id: str, input_text: str):
        """Dự đoán từ mô hình

        Args:
            task_id (str): ID của task đã được đăng ký
            input_text (str): Truy vấn đầu vào để model thực hiện task

        Raises:
            NotImplementedError: phương thức này cần được triển khai trong lớp con
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
        raise NotImplementedError(
            "Phương thức predict cần được triển khai trong lớp con."
        )

    @abstractmethod
    def register_task(
        self,
        task_id: str,
        prompt: str,
        required_keys: list[str] | None = None,
        output_type: str = "json",
        max_new_tokens: int = 128,
    ):
        """Đăng ký task mới cho model.

        Args:
            task_id (str): ID của task
            prompt (str): prompt để mô hình thực hiện task
            required_keys (list[str], optional): danh sách các trường bắt buộc trong output. Defaults to None.
            output_type (str, optional): loại output mong muốn. Defaults to "json".
            max_new_tokens (int, optional): số lượng token tối đa được sinh ra. Defaults to 128.

        Raises:
            NotImplementedError: phương thức này cần được triển khai trong lớp con
        """
        raise NotImplementedError(
            "Phương thức register_task cần được triển khai trong lớp con."
        )


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

    def register_task(
        self,
        task_id: str,
        prompt: str,
        required_keys: list[str] | None = None,
        output_type: str = "json",
        max_new_tokens: int = 128,
    ):
        """Đăng ký task mới cho model

        Args:
            task_id (str): mã task để model phân biệt khi suy luận
            prompt (str): nội dung tùy chỉnh yêu cầu cho mỗi của mỗi task
            required_keys (list[str] | None, optional): các keys trả về bắt buộc nếu là json. Defaults to None.
            output_type (str, optional): định dạng output mong muốn (list, json, boolean, str, int). Defaults to "json".
            max_new_tokens (int, optional): Số tokens mới tối đa được sinh ra. Defaults to 128.
        """

        self.tasks[task_id] = {
            "prompt": prompt,
            "required_keys": required_keys or [],
            "output_type": output_type,
            "max_new_tokens": max_new_tokens,  # Có thể điều chỉnh nếu cần
        }

        logger.info(
            f"Đã đăng ký task mới: {task_id} với prompt: {prompt} và required_keys: {required_keys}"
        )

    def build_messages(self, task_id: str, input_text: str) -> list[dict[str, str]]:
        """Tạo template message cho model

        Args:
            task_id (str): Task đã đăng ký giúp model nhận biết để task để thực hiện
            input_text (str): Truy vấn đầu vào để model thực hiện task (có thể là câu hỏi pháp luật, văn bản pháp luật, hoặc ngữ cảnh đã )

        Raises:
            CustomException: Nếu task_id chưa được đăng ký trong self.tasks

        Returns:
            list[dict[str, str]]: Danh sách các message được tạo ra gồm role và content, giúp model nhận biết task và input_text để thực hiện task
        """
        task = self.tasks.get(task_id)
        if task is None:
            raise CustomException(
                message=f"Task chưa được đăng ký: {task_id}", status_code=500
            )

        return [
            {"role": "system", "content": Prompt.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (f"{task['prompt']}\n\n" f"input: {input_text}"),
            },
        ]

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

        if task["output_type"] not in ["json", "list"]:
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
