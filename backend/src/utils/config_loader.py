import os
import yaml
from .logger import setup_logger

# Lấy đường dẫn gốc của dự án để gọi file config ở bất kỳ đâu cũng không bị lỗi đường dẫn
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

logger = setup_logger("ConfigLoader")

def load_yaml_config(config_name="config.yaml"):
    """
    Hàm tiện ích để đọc file cấu hình YAML.
    Mặc định trỏ vào thư mục config/ ở gốc dự án.
    """
    config_path = os.path.join(PROJECT_ROOT, "config", config_name)
    
    # logger = setup_logger("ConfigLoader")
    
    if not os.path.exists(config_path):
        logger.error(f"❌ KHÔNG TÌM THẤY FILE CONFIG: {config_path}")
        raise FileNotFoundError(f"Vui lòng tạo file {config_name} trong thư mục config/")
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        # logger.info(f"✅ Đã nạp thành công cấu hình từ: {config_name}")
        
        # Debug config
        logger.info(f"--- Cấu hình từ {os.path.basename(config_path)} ---")
        for key, value in config.items():
            logger.info(f"{key}: {value}")
        
        return config
    except Exception as e:
        # logger.error(f"❌ LỖI ĐỌC FILE CONFIG {config_name}: {e}")
        raise Exception(f"Đã xảy ra lỗi khi đọc file config: {e}")