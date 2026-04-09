# /tests/test_lp_parser.py
"""
Pytest suite for lp_parser.py — covers real-world user input formats.
All constraint counts are verified against actual parser output.

Note: "x, y >= 0" → expands to x>=0 and y>=0 = 2 constraints
      "x1, x2, x3 >= 0" → expands to 3 constraints
"""
import pytest
from app.nlp.parsers.lp_parser import parse_lp_problem_from_string


# ─────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────

def assert_parsed(result, obj_type: str, n_vars: int, n_constraints: int):
    assert result is not None, "Parser returned None — parse failed"
    assert result["objective_type"] == obj_type, \
        f"Expected obj_type={obj_type}, got {result['objective_type']}"
    assert len(result["objective_coeffs_map"]) == n_vars, \
        f"Expected {n_vars} variables, got {len(result['objective_coeffs_map'])}"
    assert len(result["constraints"]) == n_constraints, \
        f"Expected {n_constraints} constraints, got {len(result['constraints'])}: {result['constraints']}"


# ─────────────────────────────────────────────────
# BASIC CASES
# ─────────────────────────────────────────────────

class TestBasicParsing:

    def test_english_maximize_subject_to(self):
        """Standard format with bullet dashes."""
        text = (
            "Maximize: 3x + 2y\n"
            "Subject to:\n"
            "- x + y <= 10\n"
            "- 2x + y <= 15\n"
            "- x, y >= 0"   # expands to 2 constraints → total 4
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 4)
        assert result["objective_coeffs_map"]["x"] == pytest.approx(3.0)
        assert result["objective_coeffs_map"]["y"] == pytest.approx(2.0)
        # Verify bullet dashes didn't flip signs
        c1 = next(c for c in result["constraints"] if c["rhs"] == 10.0)
        assert c1["coeffs_map"]["x"] == pytest.approx(1.0), "Bullet '-' should not negate x"

    def test_english_minimize_subject_to(self):
        text = (
            "Minimize chi phí: 4x + 3y\n"
            "Subject to:\n"
            "- 2x + y >= 8\n"
            "- x + 2y >= 7\n"
            "- x, y >= 0"   # +2 → total 4
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "minimize", 2, 4)

    def test_vietnamese_toi_da_hoa(self):
        text = (
            "Tôi muốn tối đa hóa lợi nhuận: 3x + 2y\n"
            "Với điều kiện:\n"
            "- x + y <= 10\n"
            "- 2x + y <= 15\n"
            "- x, y >= 0"   # +2 → total 4
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 4)

    def test_vietnamese_toi_da_abbreviation(self):
        """'tối đa' (không có 'hóa') phải được nhận diện."""
        text = (
            "tối đa: 5x1 + 4x2\n"
            "với điều kiện:\n"
            "x1 <= 4\n"
            "2x2 <= 12\n"
            "3x1 + 2x2 <= 18\n"
            "x1, x2 >= 0"   # +2 → total 5
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 5)

    def test_three_variables(self):
        text = (
            "Minimize: 2*x1 + 3*x2 + 1.5*x3\n"
            "Subject to:\n"
            "- x1 + x2 + x3 >= 1000\n"
            "- x1 >= 200\n"
            "- x2 <= 300\n"
            "- x1, x2, x3 >= 0"   # +3 → total 6
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "minimize", 3, 6)

    def test_inline_comma_separated(self):
        """Format: 'Maximize 2x + 4y, x + 2y <= 100, 2x + y <= 100'"""
        text = "Maximize 2x + 4y, x + 2y <= 100, 2x + y <= 100, x, y >= 0"
        result, logs = parse_lp_problem_from_string(text)
        assert result is not None
        assert result["objective_type"] == "maximize"


# ─────────────────────────────────────────────────
# BUG-1 + BUG-3: TRAILING METHOD TEXT
# ─────────────────────────────────────────────────

class TestTrailingMethodText:
    """Parser phải bỏ qua cụm chỉ phương pháp ở cuối message."""

    def test_trailing_2_pha(self):
        text = (
            "Tôi muốn tối đa hóa lợi nhuận: 3x + 2y\n"
            "Với điều kiện:\n"
            "- x + y <= 10\n"
            "- 2x + y <= 15\n"
            "- x, y >= 0\n"
            "bằng phương pháp 2 pha"
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 4)

    def test_trailing_hai_pha(self):
        text = (
            "Maximize: 3x + 5y\n"
            "Subject to:\n"
            "x + y <= 10\n"
            "x, y >= 0\n"
            "bằng phương pháp hai pha"
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 3)

    def test_trailing_simplex(self):
        text = (
            "Maximize: x + 2y\n"
            "Subject to:\n"
            "x - y <= 10\n"
            "x, y >= 0\n"
            "using simplex"
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 3)

    def test_trailing_hinh_hoc(self):
        text = (
            "tối đa 3x + 2y\n"
            "với điều kiện:\n"
            "x + y <= 10\n"
            "x, y >= 0\n"
            "bằng hình học"
        )
        result, logs = parse_lp_problem_from_string(text)
        assert_parsed(result, "maximize", 2, 3)


# ─────────────────────────────────────────────────
# INVALID / FAIL CASES
# ─────────────────────────────────────────────────

class TestInvalidInput:

    def test_random_text_returns_none(self):
        text = "Xin chào, thời tiết hôm nay thế nào?"
        result, logs = parse_lp_problem_from_string(text)
        assert result is None

    def test_no_objective_keyword_returns_none(self):
        text = "x + y <= 10\n2x + y <= 15"
        result, logs = parse_lp_problem_from_string(text)
        assert result is None

    def test_objective_no_math_expression(self):
        """Objective keyword present but no constraints at all → empty constraints list."""
        text = "Maximize: 100 + 200"   # pure numbers, no variables → no coeffs_map
        result, logs = parse_lp_problem_from_string(text)
        # Either parse fails (no variable names) or succeeds with 0 constraints
        if result is not None:
            assert len(result["constraints"]) == 0
