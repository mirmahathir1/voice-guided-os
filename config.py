"""
Configuration management for the text-guided desktop controller.
Loads environment variables and defines system-wide settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (same directory as config.py)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Note: API key will be validated when LLM client is initialized (Phase 4)

# LLM Model Configuration
LLM_MODEL = "gpt-4o"  # Using gpt-4o as gpt-5.2 may not be available
LLM_TEMPERATURE = 0.0  # Deterministic responses
LLM_MAX_TOKENS = 256  # Sufficient for JSON responses

# Grid Configuration
GRID_ROWS = 10  # A-J
GRID_COLS = 10  # 1-10
REFINEMENT_ROWS = 2  # A-B
REFINEMENT_COLS = 2  # 1-2

# Click Marker Configuration
CLICK_MARKER_COLOR = "red"
CLICK_MARKER_RADIUS = 15  # pixels

# Execution Logging Configuration
EXECUTION_LOG_DIR = "execution"

# Action Loop Configuration
MAX_ITERATIONS = 20  # Prevent infinite loops
ACTION_DELAY_SECONDS = 1.0  # Wait time after each action

# Python Executable Path
PYTHON_EXECUTABLE = "./env/bin/python"
