# postgres-mcp

PostgreSQL natural language query MCP server.

## Quick start

```bash
cd ~/Documents/VibeCoding/Week5
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
cp config/config.example.yaml config/config.yaml
python -m postgres_mcp
```

## Project layout

```text
src/postgres_mcp/    # application package
tests/              # unit/integration/contract tests
config/             # configuration files
logs/               # runtime logs
```

## Development

```bash
ruff format .
ruff check .
mypy src/ --strict
pytest
```
