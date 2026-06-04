# =====================================================
# Stage 1: Frontend builder — build React SPA bằng Node
# =====================================================
FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend

# Cài deps trước (tận dụng cache layer khi chỉ đổi source)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Build: vite base='/app/' xuất ra ../static/app => /build/static/app
COPY frontend/ ./
RUN npm run build

# =====================================================
# Stage 2: Python builder — cài dependencies nặng
# =====================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off

# Cài build tools & CBC solver
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc g++ coinor-cbc coinor-libcbc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy và install requirements
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

# =====================================================
# Stage 3: Runtime — image nhỏ gọn cho production
# =====================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Chỉ cài CBC runtime + curl (cho healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends coinor-cbc curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy các packages Python đã build
COPY --from=builder /install /usr/local

# Copy source code backend
COPY . .

# Copy SPA React đã build (từ stage 1) — ghi đè static/app
COPY --from=frontend-builder /build/static/app ./static/app

EXPOSE 8000

CMD sh -c "uvicorn main:app --host ${SERVER_HOST:-0.0.0.0} --port ${SERVER_PORT:-8000}"
