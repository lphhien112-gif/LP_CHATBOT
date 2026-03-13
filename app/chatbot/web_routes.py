# /app/chatbot/web_routes.py

import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse # Thêm JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
from typing import Dict, Optional
from .dialog_manager import DialogManager 
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

if not TEMPLATES_DIR.exists():
    logger.error(f"Templates directory not found at: {TEMPLATES_DIR}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Loại bỏ bộ nhớ cấp ứng dụng local khi chạy Container hóa
# Nhưng NÊN GIỮ LẠI LÀM FALLBACK cho môi trường Development Local khi Redis tắt
active_sessions_fallback: Dict[str, DialogManager] = {}

async def get_dialog_manager(
    request: Request,
    redis_client = Depends(get_redis_client)
) -> DialogManager:
    # Lấy IP hoặc định danh client làm session id đơn giản
    client_ip = request.client.host if request.client else settings.UNKNOWN_CLIENT_ID
    session_id = f"{settings.SESSION_ID_PREFIX}{client_ip}"
    
    # --- Ưu tiên 1: Redis (production) ---
    if redis_client:
        dm = DialogManager(user_id=session_id)
        raw_state = await redis_client.get(session_id)
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
        return dm

    # --- Ưu tiên 2: RAM Fallback (local dev khi Redis tắt) ---
    # Tái sử dụng instance cũ nếu đã tồn tại, tránh tạo mới mỗi request
    if session_id in active_sessions_fallback:
        return active_sessions_fallback[session_id]
    
    logger.info(f"Tạo phiên Chatbot RAM Fallback cho: {session_id}")
    dm = DialogManager(user_id=session_id)
    active_sessions_fallback[session_id] = dm
    return dm


# --- Lưu Session Helper ---
async def save_session_to_redis(dm: DialogManager, redis_client):
    if redis_client:
        try:
            state_data = json.dumps({
                "state": dm.state,
                "logs": dm.logs
            })
            await redis_client.setex(dm.user_id, settings.SESSION_TIMEOUT, state_data) # Hết hạn theo cấu hình
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
        
    return templates.TemplateResponse(request, "index.html")

from fastapi.responses import StreamingResponse

# !!! QUAN TRỌNG: Đổi send_message_to_bot thành async def để hỗ trợ Streaming !!!
@router.post("/send_message", summary="Gửi tin nhắn đến chatbot (Streaming SSE)")
async def send_message_to_bot(
    message: str = Form(...), 
    dm: DialogManager = Depends(get_dialog_manager),
    redis_client = Depends(get_redis_client)
):
    logger.info(f"Received message via POST: '{message}' for user '{dm.user_id}'")
    if not message.strip():
        # Trả về kết quả JSON cứng qua SSE
        async def err_gen():
            yield f"data: {json.dumps({'type': 'complete', 'result': {'bot_response': {'text_response': 'Vui lòng nhập gì đó!', 'plot_image_base64': None, 'suggestions': []}}})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")
        
    async def event_generator():
        try:
            async for event in dm.handle_message(message):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.exception(f"Lỗi khi xử lý tin nhắn từ user: {e}")
            yield f"data: {json.dumps({'type': 'complete', 'result': {'bot_response': {'text_response': 'Xin lỗi, đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại hoặc đặt câu hỏi theo cách khác.', 'plot_image_base64': None, 'suggestions': ['Thử lại', 'Giải bài toán mẫu']}}})}\n\n"
        finally:
            # Save State vào Redis sau khi stream xong
            await save_session_to_redis(dm, redis_client)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/reset_chat_session", summary="Reset trạng thái hội thoại của chatbot cho user hiện tại")
async def reset_session(
    dm: DialogManager = Depends(get_dialog_manager),
    redis_client = Depends(get_redis_client)
):
    logger.info(f"Resetting chat session for user '{dm.user_id}'.")
    dm.reset_state()
    await save_session_to_redis(dm, redis_client)
    
    initial_message = dm.state.get("last_bot_message", "Đã làm mới. Bạn muốn bắt đầu lại chứ?")
    return {"bot_response": {"text_response": initial_message, "plot_image_base64": None, "suggestions": ["Nhập bài toán mới"]}}

