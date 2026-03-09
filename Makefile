.PHONY: setup update clean run test docker-build docker-up docker-down

# Local Development Commands
setup:
	python -m venv venv
	venv/Scripts/pip install -r requirements.txt
	venv/Scripts/playwright install chromium

run:
	venv/Scripts/python main.py

test:
	venv/Scripts/pytest tests/ -v

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf logs/*.log

# Docker Commands
docker-build:
	docker build -t lp_chatbot .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f
