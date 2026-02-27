#!/bin/bash
set -e

echo "🔧 Setting up Nura development environment..."

# Install Nura in editable mode with all extras (uv will auto-create .venv)
uv pip install -e ".[all]"

# Install dev dependencies
uv pip install -r requirements-dev.txt

echo "✅ Development environment ready!"
echo "Use 'uv run python' or 'uv run pytest' to execute commands."
