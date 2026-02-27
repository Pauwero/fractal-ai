"""Configuration loading and validation.

Loads strategy configs, tolerances, session definitions, and pair parameters
from JSON files in the config/ directory. Validates against Pydantic schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Config directory relative to project root
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_json_config(filename: str) -> dict[str, Any]:
    """Load a JSON configuration file from the config directory.

    Args:
        filename: Name of the JSON file (e.g., 'tolerances.json').

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = CONFIG_DIR / filename
    with open(path) as f:
        return json.load(f)
