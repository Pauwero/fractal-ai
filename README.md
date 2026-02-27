# Fractal AI

Systematic forex trading platform using ICT/Fractal methodology.

## Status

🏗️ **Phase M0: Foundation** — Project skeleton and development environment.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Start API (development)
uvicorn src.api.main:app --reload

# Or use Docker
docker compose up
```

## Architecture

Domain-Driven Design with 6 bounded contexts. See `docs/architecture/BLUEPRINT.md`.

## Documentation

- `CLAUDE.md` — AI agent project context
- `docs/GLOSSARY.md` — Ubiquitous language
- `docs/architecture/BLUEPRINT.md` — Full architectural blueprint
- `docs/strategies/` — Strategy playbooks
