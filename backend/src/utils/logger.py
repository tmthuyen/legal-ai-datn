import logging
import os
from datetime import datetime

def setup_logger(name="project_logger", filename=None):
    # 1. Tạo thư mục logs nếu chưa có
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 2. Tạo tên file log theo ngày tháng (VD: logs/train_2026-02-23.log)
    if filename is None:
        current_time = datetime.now().strftime("%Y-%m-%d")
        log_file = f"logs/{name}_{current_time}.log"
    else: 
        log_file = f"logs/{filename}"
        
    

    # 3. Cấu hình logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Bắt mọi cấp độ log

    # Tránh bị nhân đôi dòng log nếu gọi nhiều lần
    if not logger.handlers:
        # 4. Định dạng dòng log cho đẹp (Thời gian - Cấp độ - Tên File - Lời nhắn)
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(filename)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 5a. Ghi ra màn hình (thay thế print)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 5b. Ghi âm thầm vào file text
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger