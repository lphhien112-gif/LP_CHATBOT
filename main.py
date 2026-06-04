# /main.py
# Tệp khởi động chính của ứng dụng

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# Import các thành phần từ các module đã tạo
from app.core.config import settings
from app.core.logger import setup_logging
from app.api.routes import api_router
from app.chatbot.web_routes import router as chatbot_web_router

# -- BƯỚC 1: THIẾT LẬP LOGGING --
# Phải được gọi ở đây, trước khi tạo instance của app,
# để đảm bảo logging được áp dụng cho toàn bộ ứng dụng ngay từ đầu.
setup_logging()
logger = logging.getLogger(__name__)


# -- BƯỚC 2: KHỞI TẠO ỨNG DỤNG FASTAPI --
from contextlib import asynccontextmanager
from app.core.redis import redis_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo các tài nguyên (như Redis) trước khi server nhận requests
    await redis_manager.init_redis()
    yield # Server chạy trong thời gian này
    # Đóng kết nối khi server shutdown
    await redis_manager.close()

logger.info("Initializing FastAPI application...")
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    # Cấu hình đường dẫn cho tài liệu API (Swagger UI)
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# -- BƯỚC 2.5: THIẾT LẬP BẢO MẬT (SECURITY FIX) --
# Bổ sung CORS để API an toàn, chỉ nhận request từ Origin định sẵn
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)


# -- BƯỚC 3: GẮN (MOUNT) CÁC TỆP TĨNH --
# Dòng này rất quan trọng, nó cho phép FastAPI phục vụ các tệp CSS, JS, hình ảnh...
# từ thư mục 'static' tại đường dẫn '/static'.
# Ví dụ: trình duyệt có thể truy cập /static/css/style.css
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
logger.info(f"Static files directory mounted at /{settings.STATIC_DIR}.")

# -- GẮN GIAO DIỆN REACT (SPA) ĐÃ BUILD --
# `cd frontend && npm run build` xuất ra static/app (vite base='/app/').
# html=True để StaticFiles trả index.html tại /app/ (single-page app).
from pathlib import Path as _Path
_spa_dir = _Path(settings.STATIC_DIR) / "app"
SPA_AVAILABLE = (_spa_dir / "index.html").is_file()
if SPA_AVAILABLE:
    app.mount("/app", StaticFiles(directory=str(_spa_dir), html=True), name="spa")
    logger.info("React SPA mounted at /app.")
else:
    logger.warning("React SPA chưa được build (thiếu static/app/index.html). "
                   "Hãy chạy: cd frontend && npm install && npm run build")


# -- BƯỚC 4: BAO GỒM (INCLUDE) CÁC ROUTER --

# Bao gồm router cho các API RESTful (ví dụ: /api/v1/lp/solve)
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["Backend API"])
logger.info(f"Included API router with prefix: {settings.API_V1_STR}")

# Bao gồm router xử lý chat/SSE/luyện tập ở gốc (không prefix) để JS gọi /send_message…
app.include_router(chatbot_web_router, tags=["Chatbot Web UI"])
logger.info("Included Chatbot Web UI router at root.")

# -- BƯỚC 5: ĐỊNH NGHĨA ENDPOINT GỐC (ROOT) --
from fastapi.responses import HTMLResponse

@app.get("/", include_in_schema=False)
async def read_root():
    """Endpoint gốc: chuyển hướng tới giao diện React (/app/). Nếu SPA chưa build,
    hiển thị hướng dẫn build thay vì lỗi 404."""
    if SPA_AVAILABLE:
        return RedirectResponse(url="/app/")
    return HTMLResponse(
        "<h2>Giao diện chưa được build</h2>"
        "<p>Hãy chạy: <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code> "
        "rồi tải lại trang.</p>",
        status_code=200,
    )


# -- BƯỚC 6: KHỞI CHẠY SERVER (KHI CHẠY TRỰC TIẾP TỆP NÀY) --
if __name__ == "__main__":
    logger.info(f"Starting server on http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    uvicorn.run(
        "main:app",  # Tham chiếu đến đối tượng 'app' trong tệp 'main.py'
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower(), # Đặt log level cho uvicorn
        reload=settings.DEBUG  # reload=True rất hữu ích trong môi trường development
                               # Nó sẽ tự động khởi động lại server mỗi khi bạn lưu file code.
                               # Nên đặt là False trong môi trường production.
    )

