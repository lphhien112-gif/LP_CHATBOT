.PHONY: setup update clean run test lint security coverage docker-build docker-up docker-down docker-logs

# ─────────────────────────────────────────────────
# Local Development
# ─────────────────────────────────────────────────
setup:
	python -m venv venv
	venv/Scripts/pip install -r requirements-dev.txt
	venv/Scripts/playwright install chromium

run:
	venv/Scripts/uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# ─────────────────────────────────────────────────
# Code Quality & Security
# ─────────────────────────────────────────────────
lint:
	venv/Scripts/ruff check app/ --select E,W,F --ignore E501

security:
	venv/Scripts/bandit -r app/ -ll --skip B101

# ─────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────
test:
	venv/Scripts/pytest tests/ -v

coverage:
	venv/Scripts/pytest tests/ -v \
		--cov=app \
		--cov-report=term-missing \
		--cov-report=html:test_outputs/html_coverage

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf logs/*.log
	rm -rf test_outputs/html_coverage

# ─────────────────────────────────────────────────
# Docker
# ─────────────────────────────────────────────────
docker-build:
	docker build -t lp_chatbot .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f
