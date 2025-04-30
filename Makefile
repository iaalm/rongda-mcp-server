dev:
	uv run mcp dev rongda_mcp_server/server.py

format:
	uvx isort .
	uvx black .

lint:
	uv run mypy .