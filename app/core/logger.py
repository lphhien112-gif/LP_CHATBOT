# /core/logger.py

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from .config import settings

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging():
    """
    Thiết lập cấu hình logging cho toàn bộ ứng dụng.
    - StreamHandler: in ra console (stdout)
    - RotatingFileHandler: ghi ra logs/app.log (max 5 MB, lưu 3 bản cũ)
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT
    )

    # Handler 1: Console
    # Đảm bảo console in được Unicode (tiếng Việt). Trên Windows, stdout mặc định
    # dùng cp1252 và sẽ ném UnicodeEncodeError khi log có ký tự tiếng Việt.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # Handler 2: File (rotating, max 5 MB, 3 bản lưu)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.info(f"Logging setup complete. Log level: {settings.LOG_LEVEL}. File: {LOG_FILE}")


    # Ví dụ về cách log từ các module khác:
    # import logging
    # logger = logging.getLogger(__name__)
    # logger.info("This is an info message from my_module.")
    # logger.error("This is an error message from my_module.")

if __name__ == "__main__":
    # Test thử thiết lập logging
    setup_logging()
    
    logger = logging.getLogger("my_test_logger")
    logger.debug("Đây là một thông điệp debug (sẽ không hiển thị nếu LOG_LEVEL là INFO).")
    logger.info("Đây là một thông điệp info.")
    logger.warning("Đây là một thông điệp warning.")
    logger.error("Đây là một thông điệp error.")
    logger.critical("Đây là một thông điệp critical.")

    # Thay đổi log level để xem debug message
    # settings.LOG_LEVEL = "DEBUG" # Điều này không ảnh hưởng đến setup_logging đã chạy
    # print("\nRe-setting up logging with DEBUG level (for demonstration):")
    # # Để thay đổi log level động, bạn cần cấu hình lại logger trực tiếp hoặc gọi lại setup_logging
    # # Ví dụ đơn giản là thay đổi level của root logger:
    # logging.getLogger().setLevel("DEBUG")
    # logger.debug("Bây giờ thông điệp debug này sẽ hiển thị.")
