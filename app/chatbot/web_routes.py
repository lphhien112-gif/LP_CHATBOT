# /app/chatbot/web_routes.py

import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
import json
from typing import Dict
from .dialog_manager import DialogManager
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Loại bỏ bộ nhớ cấp ứng dụng local khi chạy Container hóa
# Nhưng NÊN GIỮ LẠI LÀM FALLBACK cho môi trường Development Local khi Redis tắt
active_sessions_fallback: Dict[str, DialogManager] = {}

def _resolve_session_id(request: Request) -> str:
    """Ưu tiên header 'X-Session-Id' do client (SPA) sinh ra để mỗi trình duyệt có
    phiên riêng; nếu không có thì fallback về IP client (tương thích ngược)."""
    client_session = request.headers.get("X-Session-Id")
    if client_session:
        # Chỉ giữ ký tự an toàn để tránh chèn key độc hại vào Redis
        safe = "".join(c for c in client_session if c.isalnum() or c in "-_")[:64]
        if safe:
            return f"{settings.SESSION_ID_PREFIX}{safe}"
    client_ip = request.client.host if request.client else settings.UNKNOWN_CLIENT_ID
    return f"{settings.SESSION_ID_PREFIX}{client_ip}"


async def get_dialog_manager(
    request: Request,
    redis_client = Depends(get_redis_client)
) -> DialogManager:
    session_id = _resolve_session_id(request)
    
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

@router.post("/solve_structured", summary="Giải bài toán nhập từ FORM có cấu trúc (Streaming SSE)")
async def solve_structured(
    request: Request,
    dm: DialogManager = Depends(get_dialog_manager),
    redis_client = Depends(get_redis_client)
):
    """Nhận bài toán dạng JSON có cấu trúc từ form, đặt làm bài hiện tại rồi stream
    lời giải qua cùng pipeline với chat (tableau + giải thích)."""
    body = await request.json()
    problem = body.get("problem", {})
    solver = body.get("solver", "simple_dictionary") or "simple_dictionary"

    try:
        internal = DialogManager.build_internal_from_structured(problem)
    except Exception as e:
        logger.warning(f"solve_structured: dữ liệu không hợp lệ: {e}")
        async def err_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': f'Dữ liệu bài toán không hợp lệ: {e}'})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    dm.state["current_problem_definition"] = internal
    dm.state["expectation"] = None

    async def event_generator():
        try:
            async for event in dm._solve_current_problem(solver):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.exception(f"Lỗi khi giải bài toán có cấu trúc: {e}")
            yield f"data: {json.dumps({'type': 'complete', 'result': {'bot_response': {'text_response': 'Xin lỗi, đã xảy ra lỗi khi giải bài toán.', 'suggestions': ['Thử lại']}}})}\n\n"
        finally:
            await save_session_to_redis(dm, redis_client)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/extract_image", summary="Đọc đề bài LP từ ảnh (OCR bằng vision model)")
async def extract_image(
    request: Request,
    dm: DialogManager = Depends(get_dialog_manager),
):
    """Nhận ảnh (data URL base64), trả về văn bản đề bài để người dùng xem/sửa rồi gửi."""
    body = await request.json()
    image = body.get("image", "")
    if not image or not isinstance(image, str):
        return JSONResponse({"error": "Thiếu dữ liệu ảnh."}, status_code=400)
    if not dm.openai_client.client:
        return JSONResponse({"error": "Cần kết nối AI (vision) để đọc ảnh."}, status_code=503)
    text = await dm.openai_client.extract_lp_from_image(image)
    if not text:
        return JSONResponse({"error": "Không đọc được đề Quy hoạch tuyến tính từ ảnh. "
                                      "Hãy chụp rõ hơn hoặc tự nhập đề."}, status_code=422)
    return {"text": text}


@router.post("/practice/new", summary="Tạo một bài luyện tập mới (chế độ tutor)")
async def practice_new(
    dm: DialogManager = Depends(get_dialog_manager),
    redis_client = Depends(get_redis_client)
):
    data = dm.new_practice_problem()
    await save_session_to_redis(dm, redis_client)
    return data


@router.post("/practice/grade", summary="Chấm nghiệm sinh viên nhập cho bài luyện tập")
async def practice_grade(
    request: Request,
    dm: DialogManager = Depends(get_dialog_manager),
    redis_client = Depends(get_redis_client)
):
    body = await request.json()
    answers = body.get("answers", {})
    result = dm.grade_practice(answers)
    await save_session_to_redis(dm, redis_client)
    return result


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

