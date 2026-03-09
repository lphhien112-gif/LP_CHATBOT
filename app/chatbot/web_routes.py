# /app/chatbot/web_routes.py

import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse # Thêm JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import redis
from typing import Dict
from .dialog_manager import DialogManager 
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Khởi tạo Redis Client
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info(f"Kết nối Redis thành công tại: {settings.REDIS_URL}")
except Exception as e:
    logger.error(f"Lỗi kết nối Redis: {e}. Hệ thống sẽ không thể lưu Phiên (Session).")
    redis_client = None

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

if not TEMPLATES_DIR.exists():
    logger.error(f"Templates directory not found at: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Loại bỏ bộ nhớ cấp ứng dụng local khi chạy Container hóa
# Nhưng NÊN GIỮ LẠI LÀM FALLBACK cho môi trường Development Local khi Redis tắt
active_sessions_fallback: Dict[str, DialogManager] = {}

def get_dialog_manager(request: Request) -> DialogManager:
    # Lấy IP hoặc định danh client làm session id đơn giản
    client_ip = request.client.host if request.client else "unknown_client"
    session_id = f"web_session_{client_ip}"
    
    dm = DialogManager(user_id=session_id)
    
    # Query Redis để khôi phục State của User nếu có
    if redis_client:
        raw_state = redis_client.get(session_id)
        if raw_state:
            try:
                saved_data = json.loads(raw_state)
                dm.state = saved_data.get("state", dm.state)
                dm.logs = saved_data.get("logs", [])
                logger.debug(f"Đã phục hồi Chat Session cho: {session_id} từ Redis.")
            except json.JSONDecodeError:
                logger.error(f"Lỗi phân giải JSON từ Redis cho {session_id}")
        else:
            logger.info(f"Tạo phiên Chatbot mới trên Redis cho: {session_id}")
    else:
        # Fallback lưu trữ local memory nếu không kết nối được Redis
        if session_id not in active_sessions_fallback:
            logger.info(f"Tạo phiên Chatbot RAM Fallback cho: {session_id}")
            active_sessions_fallback[session_id] = dm
        dm = active_sessions_fallback[session_id]
            
    return dm

# --- Lưu Session Helper ---
def save_session_to_redis(dm: DialogManager):
    if redis_client:
        try:
            state_data = json.dumps({
                "state": dm.state,
                "logs": dm.logs
            })
            redis_client.setex(dm.user_id, 86400, state_data) # Hết hạn sau 24h
        except Exception as e:
            logger.error(f"Lỗi khi lưu Session vào Redis: {e}")
    else:
        # Cập nhật state vào fallback ram map
        active_sessions_fallback[dm.user_id] = dm

@router.get("/chat", response_class=HTMLResponse, summary="Giao diện chat với LP Chatbot")
async def get_chat_interface(request: Request):
    logger.info(f"Serving chat interface from template directory: {TEMPLATES_DIR}")
    index_template_path = TEMPLATES_DIR / "index.html"
    if not index_template_path.is_file():
        logger.error(f"index.html not found in {TEMPLATES_DIR}")
        return HTMLResponse(content="<h1>Lỗi: Không tìm thấy tệp index.html</h1>", status_code=500)
        
    return templates.TemplateResponse("index.html", {"request": request})

# !!! QUAN TRỌNG: Đổi send_message_to_bot thành async def !!!
@router.post("/send_message", summary="Gửi tin nhắn đến chatbot và nhận phản hồi", response_class=JSONResponse)
async def send_message_to_bot(
    message: str = Form(...), 
    dm: DialogManager = Depends(get_dialog_manager) # Sử dụng Depends để lấy instance
):
    logger.info(f"Received message via POST: '{message}' for user '{dm.user_id}'") # Log user_id
    if not message.strip():
        return {"bot_response": {"text_response": "Vui lòng nhập gì đó!", "plot_image_base64": None, "suggestions": []}}
        
    # Gọi hàm handle_message bất đồng bộ
    bot_response_data = await dm.handle_message(message) 
    
    # Save State vào Redis Network
    save_session_to_redis(dm)
    
    # Trả về toàn bộ dictionary bot_response_data
    # Frontend (JavaScript) sẽ xử lý object này
    return {"bot_response": bot_response_data}

@router.post("/reset_chat_session", summary="Reset trạng thái hội thoại của chatbot cho user hiện tại")
async def reset_session(dm: DialogManager = Depends(get_dialog_manager)):
    logger.info(f"Resetting chat session for user '{dm.user_id}'.")
    dm.reset_state()
    save_session_to_redis(dm)
    
    initial_message = dm.state.get("last_bot_message", "Đã làm mới. Bạn muốn bắt đầu lại chứ?")
    return {"bot_response": {"text_response": initial_message, "plot_image_base64": None, "suggestions": ["Nhập bài toán mới"]}}

