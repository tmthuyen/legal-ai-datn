import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

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

    # log predict

    def log_prediction_to_jsonl(
        self,
        input: str,
        response_time: float,  # Tính bằng giây (seconds) hoặc mili-giây (ms)
        raw_output: str,
        parsed_output: Dict[str, Any],
        task_id: str = "LEGAL_QUERY_REFERENCE_HIERARCHY_EXTRACTION",
        log_file_path: str = "prediction_logs.jsonl",
    ) -> None:
        """
        Ghi log kết quả dự đoán của model vào file JSONL dưới dạng append.
        """
        # Chuẩn hóa cấu trúc log theo đúng yêu cầu
        log_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "response_time": response_time,
            "input": input,
            "result": {"raw_output": raw_output, "output": parsed_output},
            "task_id": task_id,
        }

        # Đảm bảo thư mục chứa file log tồn tại
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Mở file ở chế độ append ("a") để ghi nối tiếp dòng mới
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        logger.info(f"Đã ghi log dự đoán vào {log_file_path}: {log_entry}")

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
