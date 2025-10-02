test:
  uv run pytest -v tests

agent-lint +FILES:
  @uv run pre-commit run --files {{FILES}} >/dev/null || uv run pre-commit run --files {{FILES}}
