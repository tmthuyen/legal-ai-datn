import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

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
    được đề cập rõ ràng trong query_text.

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

    @abstractmethod
    def predict(self, task_id: str, input_text: str, max_new_tokens: int = 128):
        """Thực hiện suy luận dựa trên task_id và input_text

        Args:
            task_id (str): ID của task đã được đăng ký
            input_text (str): văn bản đầu vào để suy luận
            max_new_tokens (int, optional): số lượng token tối đa được sinh ra. Defaults to 128.

        Raises:
            NotImplementedError: phương thức này cần được triển khai trong lớp con

        Returns:
            dict: kết quả suy luận
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
    ):
        """Đăng ký task mới mà không cần sửa luồng inference.

        Args:
            task_id (str): ID của task
            prompt (str): prompt để mô hình thực hiện task
            required_keys (list[str], optional): danh sách các trường bắt buộc trong output. Defaults to None.
            output_type (str, optional): loại output mong muốn. Defaults to "json".

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
                "output_type": "json",
            }
        }

        logger.info(f"Tasks đã đăng ký: {list(self.tasks.keys())}")

    def register_task(
        self,
        task_id: str,
        prompt: str,
        required_keys: list[str] | None = None,
        output_type: str = "json",
    ):
        """Đăng ký task mới mà không cần sửa luồng inference."""
        self.tasks[task_id] = {
            "prompt": prompt,
            "required_keys": required_keys or [],
            "output_type": output_type,
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
                "content": (f"{task['prompt']}\n\n" f"query_text: {input_text}"),
            },
        ]

    @torch.inference_mode()
    def predict(self, task_id: str, input_text: str, max_new_tokens: int = 128) -> dict:
        """Dự đoán từ mô hình

        Args:
            task_id (str): ID của task đã được đăng ký
            input_text (str): Truy vấn đầu vào để model thực hiện task
            max_new_tokens (int, optional): Số lượng token tối đa được sinh ra. Defaults to 128.

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

        messages = self.build_messages(task_id, input_text)

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(self.device)

        # Qwen dùng <|im_end|> để kết thúc một lượt hội thoại
        im_end_id = self.tokenizer.convert_tokens_to_ids("<|im_end|>")

        stop_ids = [self.tokenizer.eos_token_id]
        if im_end_id is not None and im_end_id not in stop_ids:
            stop_ids.append(im_end_id)

        self.model.eval()

        with torch.no_grad():
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
                repetition_penalty=1.05,
            )

        input_length = inputs["input_ids"].shape[-1]
        generated_ids = outputs[0, input_length:]

        raw_output = self.tokenizer.decode(
            generated_ids, skip_special_tokens=True
        ).strip()

        # outputs = self.model.generate(
        #     **inputs,
        #     max_new_tokens=max_new_tokens,
        #     do_sample=False,
        #     use_cache=True,
        #     eos_token_id=self.tokenizer.eos_token_id,
        #     pad_token_id=self.tokenizer.pad_token_id,
        # )

        # input_length = inputs["input_ids"].shape[1]
        # generated_ids = outputs[0, input_length:]

        # raw_output = self.tokenizer.decode(
        #     generated_ids, skip_special_tokens=True
        # ).strip()

        if task["output_type"] != "json":
            return {
                "task_id": task_id,
                "success": True,
                "message": "Thành công",
                "status_code": 200,
                "result": {
                    "raw_output": raw_output,
                    "output": raw_output,
                },
            }

        try:
            decoder = json.JSONDecoder()
            start = raw_output.find("{")

            if start == -1:
                logger.error("Không tìm thấy '{' trong output. Trả về raw_output.")
                return {
                    "task_id": task_id,
                    "success": False,
                    "message": "Không tìm thấy '{' trong output. Trả về raw_output.",
                    "status_code": 500,
                    "result": {
                        "raw_output": raw_output,
                        "output": None,
                    },
                }

            result, _ = decoder.raw_decode(raw_output[start:])

        except json.JSONDecodeError:
            logger.error(
                f"JSONDecodeError: Không thể parse output thành JSON. Trả về raw_output. Output: {raw_output}"
            )
            return {
                "task_id": task_id,
                "success": False,
                "message": "JSONDecodeError: Không thể parse output thành JSON. Trả về raw_output.",
                "status_code": 500,
                "result": {
                    "raw_output": raw_output,
                    "output": None,
                },
            }

        required_keys = task["required_keys"]
        if not isinstance(result, dict):
            return {
                "task_id": task_id,
                "success": False,
                "message": "Output không phải là một đối tượng JSON",
                "status_code": 500,
                "result": {
                    "raw_output": raw_output,
                    "output": None,
                },
            }

        missing_keys = [key for key in required_keys if key not in result]

        if missing_keys:
            return {
                "task_id": task_id,
                "success": False,
                "message": f"Output thiếu các trường bắt buộc: {', '.join(missing_keys)}",
                "status_code": 500,
                "result": {
                    "raw_output": raw_output,
                    "output": result,
                },
            }

        return {
            "task_id": task_id,
            "success": True,
            "message": "Thành công",
            "status_code": 200,
            "result": {
                "raw_output": raw_output,
                "output": result,
            },
        }
