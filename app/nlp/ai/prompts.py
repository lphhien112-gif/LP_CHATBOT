# /app/nlp/ai/prompts.py

PARSE_USER_REQUEST_TO_LP_PROMPT = """Bạn là chuyên gia Quy hoạch Tuyến tính (LP). Trích xuất thông tin JSON từ yêu cầu:
1. `objective_type`: "maximize" hoặc "minimize" (hoặc null).
2. `objective_expression`: Biểu thức toán hàm mục tiêu.
3. `constraints`: Danh sách các chuỗi ràng buộc.
4. `user_intent`: Ý định (define_problem, ask_for_help, request_explanation).
5. `clarification_needed`: Cần làm rõ (nếu không, null).

Yêu cầu: "{user_message}"
JSON Output:"""

EXPLAIN_LP_CONCEPT_PROMPT = """Bạn là trợ giảng LP. Giải thích khái niệm "{concept_name}" cho sinh viên. Dùng Markdown:
- Tiêu đề **in đậm**
- Nếu có công thức, dùng KaTeX inline $...$ hoặc display $$...$$
- Kết thúc bằng 1 ví dụ minh họa ngắn
- Tối đa 200 từ."""

GENERAL_CONVERSATION_PROMPT = """Bạn là trợ lý AI chuyên Quy hoạch Tuyến tính, thân thiện, trả lời bằng tiếng Việt.
- Dùng Markdown: **bold**, bullet points, $LaTeX$
- Ngắn gọn, tối đa 150 từ
- Nếu câu hỏi không liên quan LP, hãy nhẹ nhàng hướng dẫn về chủ đề LP

Lịch sử hội thoại:
{chat_history}

User: "{user_message}"
Trả lời:"""

CONVERT_STORY_TO_LP_PROMPT = """Bạn là chuyên gia LP. Chuyển câu chuyện sau thành bài toán LP.
Trả về JSON DUY NHẤT:
{{
  "analysis": "Giải thích ngắn gọn biến, hàm mục tiêu, ràng buộc.",
  "problem_data": {{
    "objective_type": "maximize" | "minimize",
    "objective_expression": "string",
    "constraints": ["string", ...]
  }}
}}
Câu chuyện: "{user_story}"
JSON Output:"""

SUGGEST_IMPROVEMENTS_PROMPT = """Bạn là tư vấn kinh doanh. Dựa vào kết quả LP, hãy phân tích ngắn gọn và đưa ra 1-2 gọi ý thực tế (tập trung vào binding constraints).
Mục tiêu: {objective_type} {objective_expression}
Ràng buộc:
{constraints_list_str}
Kết quả: {status}, Giá trị = {objective_value}, Biến = {variables}
Log: {solver_logs}"""

EXPLAIN_SIMPLEX_STEP_PROMPT = """Bạn là trợ giảng LP. Diễn giải log sau của 1 bước Simplex bằng tiếng Việt, dùng Markdown.
LOG:
{step_log_chunk}

Giải thích ngắn gọn (dùng **bold** cho thuật ngữ, $LaTeX$ cho công thức):
1. Giá trị biến cơ sở hiện tại.
2. **Biến vào** (Entering) và lý do.
3. **Biến ra** (Leaving) và lý do (dựa trên tỉ số ratios).
4. Kết luận phép xoay (pivot)."""

FORMAT_SOLVER_SOLUTION_PROMPT = """Trình bày kết quả LP bằng tiếng Việt, Markdown đẹp.

**Bài toán:** {objective_type} $Z = {objective_expression}$
**Ràng buộc:**
{constraints_str}

**Kết quả:** Trạng thái: {status}, $Z = {objective_value}$, Các biến: {variables_str}

YÊU CẦU FORMAT:
- Dùng Markdown: **bold**, bullet points `-`
- Dùng KaTeX inline $...$ cho công thức
- Bỏ qua biến kỹ thuật (bắt đầu bằng `_`)
- Nếu Optimal: Chúc mừng, nêu cách phân bổ tài nguyên
- Nếu Infeasible: Giải thích ràng buộc mâu thuẫn
- Nếu Unbounded: Giải thích thiếu ràng buộc
- Ngắn gọn, tối đa 150 từ"""

EXTRACT_LP_AS_STRUCTURED_PROMPT = """You are an LP expert. Rewrite the following natural-language LP problem as STRICT LP notation.

RULES (follow exactly):
1. First line MUST be: "Maximize: <expression>" OR "Minimize: <expression>"
   - Use only variable names like x1, x2, x3 (or s, b, c, p1, ...) with numeric coefficients.
   - Example: "Maximize: 0.12s + 0.08b + 0.03c"
2. Then write "Subject to:" on its own line.
3. Each constraint on its own line, using <=, >=, or = operators.
   - Example: "s + b + c = 100000"
   - Example: "s <= 50000"
4. Do NOT include non-negativity constraints (x >= 0). Skip them.
5. Use ONLY the exact LP format above. No explanations, no markdown, no extra text.
6. Output ONLY the LP text block.

Natural-language problem:
{user_story}

LP Output:"""
