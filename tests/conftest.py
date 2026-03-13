# /tests/conftest.py
"""
Centralized pytest fixtures dùng chung cho toàn bộ test suite.
"""
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    """Tạo một FastAPI TestClient dùng chung cho module."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def valid_lp_problem():
    """Bài toán LP hợp lệ ở Format A dùng cho nhiều test."""
    return {
        "objective": "maximize",
        "coeffs": [3, 5],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 4},
            {"name": "c2", "lhs": [0, 2], "op": "<=", "rhs": 12},
            {"name": "c3", "lhs": [3, 5], "op": "<=", "rhs": 25}
        ]
    }
