# /app/nlp/ai/openai_client.py
import sys
import os
import logging
import json
import re
from typing import Dict, Any, Optional, List

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import OpenAI library
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
    logging.warning("Thư viện openai chưa được cài đặt.")

# Import prompts
from app.nlp.ai.prompts import (
    PARSE_USER_REQUEST_TO_LP_PROMPT,
    EXPLAIN_LP_CONCEPT_PROMPT,
    GENERAL_CONVERSATION_PROMPT,
    CONVERT_STORY_TO_LP_PROMPT,
    SUGGEST_IMPROVEMENTS_PROMPT,
    EXPLAIN_SIMPLEX_STEP_PROMPT,
    FORMAT_SOLVER_SOLUTION_PROMPT,
    EXTRACT_LP_AS_STRUCTURED_PROMPT,
    GENERATE_EXERCISE_PROMPT,
    EXTRACT_LP_FROM_IMAGE_PROMPT,
)


logger = logging.getLogger(__name__)

class OpenAiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None,
                 base_url: Optional[str] = None):
        """
        Khởi tạo client LLM (tương thích OpenAI, hỗ trợ proxy base_url).

        Đọc cấu hình từ biến môi trường, chấp nhận cả tên chuẩn của SDK lẫn tên rút gọn:
          - API key:  OPENAI_API_KEY  ||  API_KEY
          - Base URL: OPENAI_BASE_URL ||  BASE_URL   (để trỏ tới proxy tương thích OpenAI)
          - Model:    MODEL_NAME      ||  OPENAI_MODEL
        Tham số truyền trực tiếp (nếu có) sẽ được ưu tiên hơn biến môi trường.
        """
        self.logs: List[str] = []
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")
        self.model_name = model_name or os.getenv("MODEL_NAME") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "15.0"))
        self.client: Optional[AsyncOpenAI] = None

        if not AsyncOpenAI:
            self._log("Lỗi: Thư viện 'openai' không được tìm thấy.")
            return

        if self.api_key:
            try:
                client_kwargs: Dict[str, Any] = {"api_key": self.api_key, "timeout": self.timeout}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self.client = AsyncOpenAI(**client_kwargs)
                self._log(
                    f"Đã cấu hình client LLM thành công: model='{self.model_name}', "
                    f"base_url='{self.base_url or 'mặc định (api.openai.com)'}'."
                )
            except Exception as e:
                self._log(f"Lỗi khi cấu hình client LLM: {e}")
                self.client = None
        else:
            self._log("Cảnh báo: API Key cho LLM không được cung cấp (đặt OPENAI_API_KEY hoặc API_KEY).")

    def _log(self, message: str):
        self.logs.append(message)
        logger.info(f"OpenAiClient: {message}")

    async def _call_llm_api(self, prompt: str) -> Optional[str]:
        self.logs.clear()
        if not self.client:
            self._log("Lỗi: Model LLM (OpenAI) chưa được khởi tạo.")
            return None

        self._log(f"Đang gửi prompt tới LLM '{self.model_name}': '{prompt[:200]}...'")
        try:
            import asyncio
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=self.timeout + 2.0  # Cộng thêm 2s buffer cho network timeout
            )
            
            if response.choices and len(response.choices) > 0:
                result_text = response.choices[0].message.content
                if result_text:
                    self._log("LLM đã tạo văn bản.")
                    return result_text.strip()
            
            self._log(f"Cấu trúc phản hồi LLM không như mong đợi: {response}")
            return None
            
        except asyncio.TimeoutError:
            self._log(f"Lỗi: Timeout khi gọi API OpenAI (quá {self.timeout} giây).")
            return None
        except Exception as e:
            self._log(f"Lỗi khi gọi API LLM: {e}")
            return None

    async def _call_llm_api_stream(self, prompt: str, temperature: float = 0.5):
        self.logs.clear()
        if not self.client:
            self._log("Lỗi: Client AI chưa được khởi tạo.")
            yield "Xin lỗi, hệ thống AI đang gặp sự cố kết nối."
            return

        self._log(f"Đang gửi prompt (Stream) tới OpenAI ({self.model_name})...")
        try:
            import asyncio
            # Nếu model là gpt-5, loại bỏ temperature (gpt-5 chỉ hỗ trợ mặc định 1.0)
            kwargs = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True
            }
            if not self.model_name.startswith("gpt-5"):
                kwargs["temperature"] = temperature

            # Bảo vệ thời điểm thiết lập stream bằng timeout (giống bản non-stream)
            # để tránh treo vô hạn khi server không phản hồi.
            stream = await asyncio.wait_for(
                self.client.chat.completions.create(**kwargs),
                timeout=self.timeout + 2.0
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            self._log("Dòng dữ liệu Stream đã kết thúc thành công.")
        except asyncio.TimeoutError:
            self._log(f"Lỗi: Timeout khi thiết lập stream OpenAI (quá {self.timeout} giây).")
            yield "\nXin lỗi, yêu cầu tới AI bị quá thời gian chờ. Vui lòng thử lại."
        except Exception as e:
            self._log(f"Lỗi khi gọi OpenAI API (Stream): {e}")
            yield f"\nĐã có lỗi xảy ra trong quá trình nhận dữ liệu từ AI: {e}"
            
    async def _call_llm_for_json(self, prompt: str) -> Optional[Dict]:
        response_str = await self._call_llm_api(prompt)
        if not response_str:
            return None
        
        try:
            # Trích xuất JSON từ khối mã markdown
            json_match = re.search(r"```json\s*([\s\S]+?)\s*```", response_str, re.IGNORECASE)
            json_str = json_match.group(1) if json_match else response_str
            return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError) as e:
            self._log(f"Lỗi khi giải mã JSON từ phản hồi LLM: {e}. Phản hồi là: {response_str}")
            return None

    async def handle_general_conversation(self, user_message: str, chat_history: List[Dict[str, str]]) -> Optional[str]:
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
        prompt = GENERAL_CONVERSATION_PROMPT.format(chat_history=history_str, user_message=user_message)
        return await self._call_llm_api(prompt)

    async def handle_general_conversation_stream(self, user_message: str, chat_history: List[Dict[str, str]]):
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
        prompt = GENERAL_CONVERSATION_PROMPT.format(chat_history=history_str, user_message=user_message)
        async for chunk in self._call_llm_api_stream(prompt, temperature=0.7):
            yield chunk

    async def parse_user_request_to_lp_structure(self, user_message: str) -> Optional[Dict[str, Any]]:
        prompt = PARSE_USER_REQUEST_TO_LP_PROMPT.format(user_message=user_message)
        return await self._call_llm_for_json(prompt)

    async def explain_lp_concept(self, concept_name: str) -> Optional[str]:
        prompt = EXPLAIN_LP_CONCEPT_PROMPT.format(concept_name=concept_name)
        return await self._call_llm_api(prompt)

    async def generate_exercise(self, hint: str = "") -> Optional[str]:
        """Sinh một bài tập LP mới (ngữ cảnh + khối Maximize/Subject to) để luyện tập."""
        prompt = GENERATE_EXERCISE_PROMPT.format(
            user_hint=(hint.strip() or "Tự chọn chủ đề và độ khó vừa phải.")
        )
        return await self._call_llm_api(prompt)

    async def extract_lp_from_image(self, image_data_url: str) -> Optional[str]:
        """Đọc đề bài LP từ ẢNH (data URL base64) bằng model vision. Trả về văn bản đề
        ở định dạng Maximize/Minimize + Subject to, hoặc None nếu lỗi/không phải LP."""
        if not self.client:
            return None
        self.logs.clear()
        self._log("Đang đọc đề từ ảnh (vision)...")
        try:
            import asyncio
            resp = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": EXTRACT_LP_FROM_IMAGE_PROMPT},
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                        ],
                    }],
                ),
                timeout=self.timeout + 15.0,  # ảnh cần thêm thời gian
            )
            if resp.choices and resp.choices[0].message.content:
                text = resp.choices[0].message.content.strip()
                if "KHONG_PHAI_LP" in text:
                    return None
                # Loại bỏ khối ```...``` nếu model bọc code fence
                text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text).strip()
                self._log("Đã đọc đề từ ảnh.")
                return text or None
            return None
        except asyncio.TimeoutError:
            self._log("Timeout khi đọc ảnh.")
            return None
        except Exception as e:
            self._log(f"Lỗi khi đọc ảnh (có thể model không hỗ trợ vision): {e}")
            return None
        
    async def convert_story_to_lp(self, user_story: str) -> Optional[Dict[str, Any]]:
        prompt = CONVERT_STORY_TO_LP_PROMPT.format(user_story=user_story)
        return await self._call_llm_for_json(prompt)

    async def extract_lp_as_structured(self, user_story: str) -> Optional[str]:
        """Convert natural-language LP problem to standard LP text notation for re-parsing.
        Returns a string like:
            Maximize: 0.12s + 0.08b\nSubject to:\ns + b <= 100000\ns <= 50000
        or None on failure.
        """
        if not self.client:
            return None
        prompt = EXTRACT_LP_AS_STRUCTURED_PROMPT.format(user_story=user_story)
        result = await self._call_llm_api(prompt)
        if result:
            self._log(f"extract_lp_as_structured → {result[:200]}")
        return result
        
    async def suggest_improvements(self, problem_context: Dict[str, Any]) -> Optional[str]:
        problem_def = problem_context.get("problem_definition", {})
        solution = problem_context.get("solution", {})
        
        prompt = SUGGEST_IMPROVEMENTS_PROMPT.format(
            objective_type=problem_def.get("objective_type", "N/A"),
            objective_expression=problem_def.get("objective_expression_str", "N/A"),
            constraints_list_str="\n".join(f"- {c}" for c in problem_def.get("constraints_str", ["N/A"])),
            status=solution.get("status", "N/A"),
            objective_value=solution.get("objective_value", "N/A"),
            variables=json.dumps(solution.get("variables", {})),
            solver_logs="\n".join(problem_context.get("logs", []))
        )
        return await self._call_llm_api(prompt)

    # --- HÀM MỚI ĐỂ GIẢI THÍCH BƯỚC GIẢI ---
    async def explain_simplex_step(self, step_log_chunk: str) -> Optional[str]:
        """Sử dụng LLM để diễn giải một đoạn log của bước giải Simplex."""
        if not self.client:
            self._log("Lỗi: Model LLM chưa được khởi tạo để giải thích bước giải.")
            return "Xin lỗi, tôi không thể phân tích ngay lúc này do lỗi kết nối AI."
            
        prompt = EXPLAIN_SIMPLEX_STEP_PROMPT.format(step_log_chunk=step_log_chunk)
        return await self._call_llm_api(prompt)

    async def explain_simplex_step_stream(self, step_log_chunk: str):
        if not self.client:
            yield "Mô hình AI chưa được thiết lập để giải thích."
            return
        prompt = EXPLAIN_SIMPLEX_STEP_PROMPT.format(step_log_chunk=step_log_chunk)
        async for chunk in self._call_llm_api_stream(prompt, temperature=0.4):
            yield chunk

    # --- HÀM FORMAT GIẢI QUYẾT BÀI TOÁN SANG VĂN XUÔI ---
    async def format_solver_solution(self, problem_def: Dict[str, Any], solution: Dict[str, Any]) -> Optional[str]:
        """Sử dụng LLM để dịch kết quả Toán học (JSON) thành văn xuôi."""
        if not self.client:
            self._log("Lỗi: Model LLM chưa được khởi tạo để format kết quả.")
            return None
            
        def _get_coeffs_str(coeffs_map):
            if not coeffs_map: return "0"
            return " + ".join([f"{v}*{k}" if k else str(v) for k, v in coeffs_map.items()])

        constraints_list = []
        for c in problem_def.get("constraints", []):
            lhs = _get_coeffs_str(c.get("coeffs_map", {}))
            op = c.get("operator", "=")
            rhs = str(c.get("rhs", 0))
            constraints_list.append(f"{lhs} {op} {rhs}")
            
        vars_map = solution.get("variables", {})
        vars_str = ", ".join([f"{k} = {v}" for k, v in vars_map.items() if not k.startswith('_')])

        prompt = FORMAT_SOLVER_SOLUTION_PROMPT.format(
            objective_type=problem_def.get("objective_type", "N/A"),
            objective_expression=problem_def.get("objective_expression_str", "N/A"),
            constraints_str="\n".join(constraints_list),
            status=solution.get("status", "N/A"),
            objective_value=solution.get("objective_value", "N/A"),
            variables_str=vars_str,
            time_taken="Không khả dụng"
        )
        return await self._call_llm_api(prompt)

    async def format_solver_solution_stream(self, problem_def: Dict[str, Any], solution: Dict[str, Any]):
        if not self.client:
            yield "Mô hình AI chưa được thiết lập để format kết quả."
            return
        
        def _get_coeffs_str(coeffs_map):
            if not coeffs_map: return "0"
            return " + ".join([f"{v}*{k}" if k else str(v) for k, v in coeffs_map.items()])

        constraints_list = []
        for c in problem_def.get("constraints", []):
            lhs = _get_coeffs_str(c.get("coeffs_map", {}))
            op = c.get("operator", "=")
            rhs = str(c.get("rhs", 0))
            constraints_list.append(f"{lhs} {op} {rhs}")
            
        vars_map = solution.get("variables", {})
        vars_str = ", ".join([f"{k} = {v}" for k, v in vars_map.items() if not k.startswith('_')])

        prompt = FORMAT_SOLVER_SOLUTION_PROMPT.format(
            objective_type=problem_def.get("objective_type", "N/A"),
            objective_expression=problem_def.get("objective_expression_str", "N/A"),
            constraints_str="\n".join(constraints_list),
            status=solution.get("status", "N/A"),
            objective_value=solution.get("objective_value", "N/A"),
            variables_str=vars_str,
            time_taken="Không khả dụng"
        )
        async for chunk in self._call_llm_api_stream(prompt, temperature=0.3):
            yield chunk
