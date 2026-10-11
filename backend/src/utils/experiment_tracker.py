import os
import json
import time
from utils.logger import setup_logger
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class ExperimentTracker:
    """
    Hỗ trợ tracking các thí nghiệm của từng model theo đúng yêu cầu:
    Lưu tại experiments/<model_name>/<timestamp>/
    """
    def __init__(self, base_dir: str = "experiments", model_name: str = "unknown_model"):
        self.base_dir = Path(base_dir)
        self.model_name = model_name
        
        # Tạo tên run bằng timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.base_dir / self.model_name / f"run_{timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logger(self.__class__.__name__)
        self.logger.info(f"Đã khởi tạo Experiment Tracker tại: {self.run_dir}")
        
    def log_config(self, config: Dict[str, Any]):
        """Lưu lại siêu tham số (hyperparameters) và config"""
        path = self.run_dir / "config.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        self.logger.info(f"Đã lưu config vào {path}")
        
    def log_metrics(self, metrics: Dict[str, float]):
        """Lưu lại các chỉ số đánh giá (metrics)"""
        path = self.run_dir / "metrics.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=4, ensure_ascii=False)
        self.logger.info(f"Đã lưu metrics vào {path}")
        
    def get_model_save_dir(self) -> str:
        """Trả về đường dẫn để model tự lưu weight của nó"""
        model_dir = self.run_dir / "model_artifacts"
        model_dir.mkdir(exist_ok=True)
        return str(model_dir)
