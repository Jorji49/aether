"""
Aether-IDE Brain — Configuration

Centralises all environment-driven settings for the sSLM Brain server.
Reads from `.env` when present, falls back to sensible defaults.

Architecture: 100% LOCAL — Ollama only, no external APIs.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the brain/ directory if present
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)


class Settings:
    """Runtime settings resolved at import time from environment variables.

    Note: OLLAMA_MODEL may be changed at runtime via the /model endpoint.
    All other fields should be treated as read-only after initialization.
    """

    # ── Ollama (local model for prompt generation) ────────────────────
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma2:2b")

    # Max tokens for generated prompts.
    # 2048 = good balance for most tasks. Increase for complex architecture prompts.
    OLLAMA_MAX_TOKENS: int = int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))

    # Temperature (0.0-1.0). Lower = focused/consistent, Higher = creative/varied.
    # 0.1 is ideal for structured coding prompts.
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))

    # ── Server ───────────────────────────────────────────────────────
    HOST: str = os.getenv("BRAIN_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("BRAIN_PORT", "8420"))

    # ── Context Scanner ──────────────────────────────────────────────
    MAX_CONTEXT_FILES: int = int(os.getenv("MAX_CONTEXT_FILES", "30"))
    MAX_FILE_SIZE_KB: int = int(os.getenv("MAX_FILE_SIZE_KB", "32"))

    # Directories / patterns to always skip during workspace scanning
    IGNORED_DIRS: frozenset[str] = frozenset({
        ".git", ".svn", ".hg",
        "node_modules", "__pycache__", ".venv", "venv",
        ".idea", ".vscode", ".vs",
        "build", "dist", "out", ".next", ".nuxt",
        "target", "bin", "obj",
    })

    IGNORED_EXTENSIONS: frozenset[str] = frozenset({
        ".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
        ".woff", ".woff2", ".ttf", ".eot",
        ".zip", ".tar", ".gz", ".rar",
        ".lock",
    })


settings = Settings()
