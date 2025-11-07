.PHONY: install run-bot run-web dev lint test

install:
pip install -e .

run-bot:
python -m main bot

run-web:
python -m main web

dev:
uvicorn app.web.main:app --reload --host 0.0.0.0 --port 8000

lint:
ruff check app tests

test:
pytest

