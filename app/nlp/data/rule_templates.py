# /app/chatbot/nlp/rule_templates.py
import re

# Các biểu thức chính quy (Regex) để phân tích văn bản
LP_PATTERNS = {
    "objective_keywords": r"(tối đa hóa|tối thiểu hóa|tối đa|tối thiểu|maximize|minimize|max|min)",
    "subject_to_keywords": r"(với điều kiện|subject to|s\.t\.|st|ràng buộc(:)?|điều kiện(:)?|với các ràng buộc)",
    "variable_coeff": r"(-?\s*\d*\.?\d*)\s*\*?\s*([a-zA-Z_][a-zA-Z0-9_]*)",
    "constraint_operator": r"(<=|>=|==|=|<|>|≤|≥)",
    "number": r"(-?\d+\.?\d*|-?\.\d+)"
}

LP_PATTERNS["full_objective_and_constraints_split"] = re.compile(
    rf"^\s*{LP_PATTERNS['objective_keywords']}\s*(.*?)\s*(?:{LP_PATTERNS['subject_to_keywords']}(.*))?$",
    re.IGNORECASE | re.DOTALL
)

LP_PATTERNS["single_constraint_line"] = re.compile(
    r"^(?:[a-zA-Z0-9\s\(\)\._-]+:)?\s*(.*?)\s*" + \
    LP_PATTERNS["constraint_operator"] + \
    r"\s*" + LP_PATTERNS["number"] + r"\s*$",
    re.IGNORECASE
)

# Từ khóa và mẫu cho Intent Recognition
INTENT_PATTERNS = {
    "greet": [re.compile(r"^\s*(xin chào|chào bạn|hello|hi|chào)\s*$", re.IGNORECASE)],
    "define_objective": [re.compile(r"^(tối đa hóa|tối thiểu hóa|maximize|minimize|max|min)\s+.*", re.IGNORECASE)],
    "add_constraint": [
        re.compile(r"^(ràng buộc|điều kiện|dk|rb|constraint).*", re.IGNORECASE),
        re.compile(r".*" + r"(<=|>=|==|=|<|>|≤|≥)" + r".*", re.IGNORECASE)
    ],
    "request_solve": [re.compile(r".*(giải|solve|kết quả|tìm lời giải).*", re.IGNORECASE)],
    "request_theoretical_concept": [
        re.compile(r".*(là gì|nghĩa là gì|define|what is)\s*$", re.IGNORECASE),
        re.compile(r"^(cho tôi biết về|nói về|explain)\s+([a-zA-Z0-9\s_À-ỹ]+)$", re.IGNORECASE)
    ],
    "request_specific_solver": [
        re.compile(
            r".*(giải\s*(bằng|lại\s*bằng|cho\s*tôi\s*bằng|theo)?|dùng|sử\s*dụng|thử|chuyển\s*(sang)?)\s+(phương\s*pháp\s+)?"
            r"(hình\s*học|đơn\s*hình|simplex|pulp|geometric|bland|auxiliary|2\s*pha|hai\s*pha|2pha|two.?phase"
            r"|đối\s*ngẫu|dual|nguyên\s*thủy|primal|phụ\s*trợ|bổ\s*trợ|cbc).*", re.IGNORECASE),
        re.compile(
            r".*bằng\s+phương\s*pháp\s+"
            r"(2\s*pha|hai\s*pha|2pha|đơn\s*hình|hình\s*học|bland|auxiliary|đối\s*ngẫu|dual\s*simplex"
            r"|dual\s*primal|nguyên\s*thủy|phụ\s*trợ|bổ\s*trợ).*", re.IGNORECASE),
        re.compile(r".*(vẽ\s*hình|vẽ\s*đồ\s*thị|giải\s*hình\s*học).*", re.IGNORECASE),
    ],
    
    # --- ✨ INTENT MỚI ĐỂ GIẢI THÍCH BƯỚC GIẢI ---
    "request_step_explanation": [
        re.compile(r".*(giải thích|phân tích)\s+(bước|vòng lặp|iteration)\s+(\d+).*", re.IGNORECASE)
    ],

    "reset_conversation": [re.compile(r"^(reset|bắt đầu lại|làm mới|clear|bài toán mới)\s*$", re.IGNORECASE)],
}

# Mẫu để trích xuất các thực thể cơ bản
ENTITY_PATTERNS = {
    # --- ✨ CẬP NHẬT: Thêm "hình học", "bland", "auxiliary" vào danh sách ---
    "solver_name": r"(pulp_cbc|geometric|simple_dictionary|simplex_bland|auxiliary|dual_simplex|dual_primal_two_phase"
                   r"|hình\s*học|pulp|bland|đơn\s*hình|đối\s*ngẫu|nguyên\s*thủy|2\s*pha|hai\s*pha|phụ\s*trợ|bổ\s*trợ|simplex|dual|primal)",
    "concept_name_lp": r"(quy tắc Bland|biến nhân tạo|simplex|đơn hình đối ngẫu)"
}

# ... các hằng số khác giữ nguyên
OBJECTIVE_TYPE_KEYWORDS = {
    "maximize": [r"tối đa hóa", r"maximize", r"max"],
    "minimize": [r"tối thiểu hóa", r"minimize", r"min"]
}
CONSTRAINT_INDICATORS = [
    r"^\s*[a-zA-Z_][a-zA-Z0-9_]*.*" + LP_PATTERNS["constraint_operator"],
    r"^\s*\d+.*" + LP_PATTERNS["constraint_operator"],
]
