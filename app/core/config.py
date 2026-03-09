# /app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Lớp quản lý cấu hình chung cho ứng dụng.
    Tất cả giá trị sẽ được tự động đọc từ biến môi trường hoặc file .env.
    Các khóa API (như OPENAI_API_KEY) được quản lý trực tiếp bằng file .env 
    và gọi thông qua os.getenv() thay vì định nghĩa tĩnh ở đây.
    """
    # Project
    PROJECT_NAME: str = "Linear Programming Chatbot"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    PORT: Optional[int] = None  # Dùng bởi một số cloud environments
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Security
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:8000"]
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # Bỏ qua các biến thừa trong .env (như API keys) để không văng lỗi
    )

# Singleton instance
settings = Settings()

