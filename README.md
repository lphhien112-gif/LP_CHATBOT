# LP_Chatbot - Trợ lý Ảo Giải Tự Động Quy Hoạch Tuyến Tính (Linear Programming)

## 1. Tổng quan dự án

**LP_Chatbot** là một hệ thống chatbot thông minh được thiết kế chuyên biệt để giúp người dùng giải quyết các bài toán tối ưu hóa trong lĩnh vực Quy hoạch tuyến tính (Linear Programming - LP). 

Hệ thống giải quyết vấn đề rào cản về mặt toán học và kỹ thuật phần mềm bằng cách cho phép người dùng nhập bài toán dưới dạng ngôn ngữ tự nhiên (Tiếng Việt hoặc Tiếng Anh). Chatbot sẽ tự động phân tích, dịch sang dạng mô hình toán học, giải bài toán từng bước và giải thích kết quả một cách trực quan, dễ hiểu.

**Công nghệ chính sử dụng:**
- **Backend:** FastAPI (Python)
- **AI / NLP:** OpenAI API (GPT models) để phân tích ngôn ngữ tự nhiên
- **LP Solver:** Các thuật toán tối ưu hóa lập trình sẵn bằng Python (Simplex, SciPy, PuLP)
- **DevOps:** Docker, Docker Compose, GitHub Actions (CI/CD)
- **Frontend:** HTML/Vanilla JS/Tailwind CSS kết hợp MathJax/KaTeX để hiển thị công thức LaTeX

## 2. Các tính năng chính

- 🤖 **Hiểu ngôn ngữ tự nhiên:** Tiếp nhận và phân tích đề bài từ ngôn ngữ nói chuyện thông thường.
- 📐 **Mô hình hóa bài toán LP:** Tự động trích xuất Hàm mục tiêu (Objective Function) và Các ràng buộc (Constraints).
- ⚙️ **Giải đa thuật toán:** Tích hợp nhiều phương pháp giải như Đơn hình (Simplex - từ điển, Bland), Đồ thị (Geometric), PuLP CBC.
- 📊 **Hiển thị chi tiết (Step-by-step):** Trình bày các bước biến đổi hệ phương trình (Dictionary format) và kiểm tra tỉ số bằng công thức Toán học chuẩn LaTeX.
- 💡 **Giải thích kết quả AI:** Tóm tắt và phân tích ý nghĩa của kết quả tối ưu bằng LLM một cách thân thiện.
- ⚡ **Streaming thời gian thực:** Phản hồi mượt mà qua luồng dữ liệu Server-Sent Events (SSE).

## 3. Kiến trúc hệ thống (Tóm tắt)

Hệ thống được thiết kế theo hướng dịch vụ (Service-Oriented) với các thành phần chính:
- **FastAPI Backend (`main.py`):** Xử lý giao tiếp HTTP/SSE và quản lý vòng đời ứng dụng.
- **Dialog Manager (`app/chatbot/dialog_manager.py`):** Đóng vai trò làm bộ não điều phối luồng trò chuyện, lưu trữ bối cảnh (context hội thoại) và gọi các module khác.
- **NLP Processing (`app/nlp/`):** Sử dụng LLM Prompt Engineering chuyên sâu kết nối qua OpenAI API để phân tách text thành định dạng JSON chuẩn bị cho Solver.
- **LP Solver (`app/solver/`):** Cốt lõi toán học, nhận bài toán đã được bóc tách và áp dụng các thuật toán bản địa để tìm nghiệm thực sự.

## 4. Hướng dẫn cài đặt nhanh (Quick Start)

Yêu cầu tiên quyết:
- Có sẵn key `OPENAI_API_KEY`.
- Clone mã nguồn về máy: `git clone <repo-url> && cd LP_CHATBOT`
- Copy file `.env.example` thành `.env` và điền cấu hình các biến môi trường (Ví dụ `OPENAI_API_KEY`).

### Cách 1: Chạy bằng Docker (Khuyên dùng)

Hệ thống đã được đóng gói sẵn với Docker Compose dành cho môi trường Productive/Testing nhanh.

```bash
# Build và chạy ngầm các container (bao gồm Web app và Redis)
docker-compose up -d --build

# Xem log xem hệ thống khởi động thành công chưa
docker-compose logs -f
```
Ứng dụng sẽ khả dụng tại trình duyệt: `http://localhost:8000`

### Cách 2: Chạy trực tiếp tại Local (Môi trường Python)

```bash
# 1. Tạo môi trường ảo
python -m venv venv

# 2. Kích hoạt môi trường ảo
# Trên Windows:
.\\venv\\Scripts\\activate
# Trên macOS/Linux:
source venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 4. Khởi động server FastAPI backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Truy cập ứng dụng tại `http://localhost:8000`.

## 5. Cấu trúc thư mục dự án

```text
LP_CHATBOT/
├── app/
│   ├── api/            # Định nghĩa các HTTP router endpoints (REST)
│   ├── chatbot/        # Chứa Dialog Manager, quản lý session và file Frontend (templates/)
│   ├── core/           # Cấu hình hệ thống chung (Settings) và các hằng số
│   ├── nlp/            # Xử lý ngôn ngữ tự nhiên, giao tiếp OpenAI API và Prompt templates
│   └── solver/         # Chứa logic thuật toán (Simplex, SciPy, PuLP) và classes chuẩn hóa model
├── logs/               # Nơi lưu trữ file log của server chạy thực tế
├── tests/              # Chứa các unit test suites bằng `pytest`
├── .env.example        # File mẫu thiết lập biến môi trường
├── docker-compose.yml  # Cấu hình chạy Docker nhiều containers
├── Dockerfile          # Image build file cho ứng dụng Backend FastAPI
├── main.py             # Entrypoint chính khởi động Uvicorn App
├── requirements.txt    # Danh sách các pip dependencies phụ thuộc
└── Makefile            # Tập hợp lệnh macro thao tác nhanh (build, test, run)
```

## 6. Cách chạy Test (Kiểm thử)

Dự án sử dụng module `pytest` để đảm bảo độ chính xác của các thuật toán toán học và luồng API.

```bash
# Chạy toàn bộ bộ test case trong dự án
pytest

# Chạy test với output chi tiết (xem rõ từng test function gõ/đậu)
pytest -v

# Chạy test chỉ định riêng cho phần thuật toán Toán Học Simplex và API
pytest tests/test_solver.py tests/test_api.py -q --tb=short
```
