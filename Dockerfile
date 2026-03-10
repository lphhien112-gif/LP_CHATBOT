# =====================================================
# Stage 1: Builder - Cài dependencies nặng
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
# Stage 2: Runtime - Image nhỏ gọn cho production
# =====================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Chỉ cài CBC runtime (không cần compiler nữa)
RUN apt-get update \
    && apt-get install -y --no-install-recommends coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy các packages đã build từ builder stage
COPY --from=builder /install /usr/local

# Copy toàn bộ source code
COPY . .

EXPOSE 8000

CMD sh -c "uvicorn main:app --host ${SERVER_HOST:-0.0.0.0} --port ${SERVER_PORT:-8000}"
