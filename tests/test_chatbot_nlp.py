# /tests/test_chatbot_nlp.py
"""
Test trích xuất LP từ văn bản tự nhiên qua parser luật (rule-based).

Lưu ý kiến trúc: hàm parser công khai là
    app.nlp.parsers.lp_parser.parse_lp_problem_from_string(text) -> (problem_data | None, logs)
và problem_data có shape:
    {
        "objective_type": "maximize" | "minimize",
        "objective_coeffs_map": {var: coeff, ...},
        "objective_variables_ordered": [...],
        "constraints": [
            {"name": "c1", "coeffs_map": {var: coeff}, "operator": "<=" | ">=" | "==", "rhs": float},
            ...
        ],
    }
"""
import pytest

from app.nlp.parsers.lp_parser import parse_lp_problem_from_string


# Mỗi case mô tả output kỳ vọng theo shape THẬT của parser (dùng coeffs_map,
# độc lập thứ tự biến). operator đã được chuẩn hóa về "<=", ">=", "==".
@pytest.mark.parametrize("text_input, expected", [
    # Case 1: Tiếng Việt, Maximize, biến x1, x2 (ràng buộc phân tách bằng dấu phẩy)
    (
        "Tối đa hóa 3x1 + 5x2 với điều kiện x1 <= 4, 2x2 <= 12, 3x1 + 2x2 <= 18",
        {
            "objective_type": "maximize",
            "objective_coeffs": {"x1": 3.0, "x2": 5.0},
            "constraints": [
                {"coeffs": {"x1": 1.0}, "operator": "<=", "rhs": 4.0},
                {"coeffs": {"x2": 2.0}, "operator": "<=", "rhs": 12.0},
                {"coeffs": {"x1": 3.0, "x2": 2.0}, "operator": "<=", "rhs": 18.0},
            ],
        },
    ),
    # Case 2: Tiếng Anh, Minimize, biến x, y, hệ số âm
    (
        "min 10x - 2y s.t. x+y>=2, 5x <= 25",
        {
            "objective_type": "minimize",
            "objective_coeffs": {"x": 10.0, "y": -2.0},
            "constraints": [
                {"coeffs": {"x": 1.0, "y": 1.0}, "operator": ">=", "rhs": 2.0},
                {"coeffs": {"x": 5.0}, "operator": "<=", "rhs": 25.0},
            ],
        },
    ),
    # Case 3: Không có dấu nhân, hệ số âm, ràng buộc đẳng thức "=="
    # (regression cho bug chuẩn hóa operator: "==" KHÔNG được biến thành "====")
    (
        "max -z + 2k subject to -5z + k == 0",
        {
            "objective_type": "maximize",
            "objective_coeffs": {"z": -1.0, "k": 2.0},
            "constraints": [
                {"coeffs": {"z": -5.0, "k": 1.0}, "operator": "==", "rhs": 0.0},
            ],
        },
    ),
])
def test_nlp_extraction(text_input, expected):
    """Kiểm tra trích xuất LP từ văn bản đúng theo shape thật của parser."""
    problem_data, logs = parse_lp_problem_from_string(text_input)

    # In logs nếu test thất bại để dễ debug
    print("Parser Logs:", logs)

    assert problem_data is not None, "Parser trả về None — parse thất bại"
    assert problem_data["objective_type"] == expected["objective_type"]

    # Hệ số hàm mục tiêu (so khớp theo tên biến, độc lập thứ tự)
    obj_map = problem_data["objective_coeffs_map"]
    assert len(obj_map) == len(expected["objective_coeffs"])
    for var, coeff in expected["objective_coeffs"].items():
        assert obj_map.get(var) == pytest.approx(coeff), f"Hệ số mục tiêu của '{var}' sai"

    # Ràng buộc (parser giữ nguyên thứ tự đầu vào)
    assert len(problem_data["constraints"]) == len(expected["constraints"])
    for actual, exp in zip(problem_data["constraints"], expected["constraints"]):
        assert actual["operator"] == exp["operator"], \
            f"Operator chuẩn hóa sai: kỳ vọng '{exp['operator']}', nhận '{actual['operator']}'"
        assert actual["rhs"] == pytest.approx(exp["rhs"])
        for var, coeff in exp["coeffs"].items():
            assert actual["coeffs_map"].get(var, 0.0) == pytest.approx(coeff), \
                f"Hệ số ràng buộc của '{var}' sai"


def test_nlp_invalid_text():
    """Văn bản không phải bài toán LP phải trả về None."""
    invalid_text = "Xin chào, thời tiết hôm nay thế nào?"
    problem_data, _ = parse_lp_problem_from_string(invalid_text)
    assert problem_data is None


def test_equality_operator_not_corrupted():
    """Regression: ràng buộc '==' phải được chuẩn hóa thành '==' (không phải '===='),
    nếu không solver sẽ từ chối với lỗi 'Unknown constraint operator'."""
    problem_data, _ = parse_lp_problem_from_string(
        "Maximize x + y subject to x + y == 10"
    )
    assert problem_data is not None
    assert len(problem_data["constraints"]) == 1
    assert problem_data["constraints"][0]["operator"] == "=="
