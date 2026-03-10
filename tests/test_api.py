# /tests/test_api.py

import pytest
from fastapi.testclient import TestClient


def test_read_root_redirects_to_chat(client: TestClient):
    """Kiểm tra endpoint gốc ('/') có chuyển hướng đến '/chat' không."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/chat"


def test_get_chat_interface(client: TestClient):
    """Kiểm tra giao diện chat có trả về HTML 200 OK không."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LP Chatbot" in response.text


def test_send_message_returns_streaming_response(client: TestClient):
    """Kiểm tra /send_message trả về streaming (SSE) HTTP 200."""
    response = client.post(
        "/send_message",
        data={"message": "xin chào"},
        headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 200
    # SSE streams dùng text/event-stream
    assert "text/event-stream" in response.headers.get("content-type", "")


def test_send_empty_message(client: TestClient):
    """Kiểm tra gửi tin nhắn rỗng trả về phản hồi hợp lý."""
    response = client.post("/send_message", data={"message": "   "})
    assert response.status_code == 200


def test_api_solve_with_valid_data(client: TestClient, valid_lp_problem):
    """Kiểm tra API solver với dữ liệu JSON hợp lệ."""
    payload = {"problem_data": valid_lp_problem, "solver_name": "pulp_cbc"}
    response = client.post("/api/v1/lp/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["solution"]["status"] == "Optimal"


def test_api_solve_with_no_data(client: TestClient):
    """Kiểm tra API solver khi không cung cấp dữ liệu nào."""
    response = client.post("/api/v1/lp/solve", json={})
    assert response.status_code == 400
    assert "problem_data" in response.text or "problem_text" in response.text
