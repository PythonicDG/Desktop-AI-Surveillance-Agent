"""
DeskMate — Configuration Loader
================================
Reads config.yaml using PyYAML and provides a singleton config object
with dot-notation access. Validates all required keys on load.

Usage:
    from utils.config_loader import config
    print(config.api.gemini_key)
"""

import sys
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Dot-notation wrapper
# ---------------------------------------------------------------------------

class ConfigNode:
    """Wraps a dictionary so keys can be accessed as attributes (dot notation).

    Supports nested dicts — each nested dict is also wrapped in a ConfigNode.
    Provides both attribute access (config.api.gemini_key) and dict-style
    access (config["api"]["gemini_key"]).
    """

    def __init__(self, data: dict) -> None:
        """Initialise a ConfigNode from a plain dictionary.

        Args:
            data: The raw dictionary to wrap.
        """
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigNode(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access — config['api']['gemini_key'].

        Args:
            key: The configuration key to look up.

        Returns:
            The configuration value.

        Raises:
            KeyError: If the key does not exist.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator — 'gemini_key' in config.api.

        Args:
            key: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        return hasattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-compatible .get() with a default value.

        Args:
            key: The configuration key to look up.
            default: Value to return if the key is missing.

        Returns:
            The configuration value, or *default* if not found.
        """
        return getattr(self, key, default)

    def to_dict(self) -> dict:
        """Convert the ConfigNode tree back to a plain dictionary.

        Returns:
            A plain dict representation of the configuration.
        """
        result: dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ConfigNode):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def __repr__(self) -> str:
        return f"ConfigNode({self.to_dict()})"


# ---------------------------------------------------------------------------
# Required-key schema
# ---------------------------------------------------------------------------
# Each entry is a dot-separated path that MUST exist in config.yaml.
# This list is checked on startup — if any key is missing the app exits
# with a clear message telling the user exactly which key to add.

REQUIRED_KEYS: list[str] = [
    "api.gemini_key",
    "api.primary_model",
    "api.fallback_model",
    "api.max_retries",
    "api.retry_delay_seconds",
    "api.timeout_seconds",
    "hotkeys.trigger",
    "capture.resize_width",
    "capture.save_last_capture",
    "capture.include_clipboard",
    "capture.monitor_index",
    "privacy.enabled",
    "ui.window_width",
    "ui.window_height",
    "ui.theme",
    "ui.font_size",
    "memory.session_history_limit",
    "memory.mistake_threshold",
    "memory.mistake_file",
    "memory.session_log_file",
    "features.timeline_enabled",
    "features.standup_enabled",
    "features.live_docs_enabled",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_path(config_path: str | None = None) -> Path:
    """Resolve the absolute path to config.yaml.

    Looks relative to the project root (the directory containing main.py).
    Accepts an explicit override for testing.

    Args:
        config_path: Optional explicit path. If *None*, defaults to
                     ``<project_root>/config.yaml``.

    Returns:
        A resolved ``Path`` object pointing at the config file.
    """
    if config_path is not None:
        return Path(config_path).resolve()
    # Project root = parent of the utils/ package
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "config.yaml"


def _validate_required_keys(raw: dict) -> list[str]:
    """Check that every key in REQUIRED_KEYS exists in the raw dict.

    Args:
        raw: The raw dictionary loaded from YAML.

    Returns:
        A list of missing key paths (empty if all present).
    """
    missing: list[str] = []
    for dotted_key in REQUIRED_KEYS:
        parts = dotted_key.split(".")
        node: Any = raw
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                missing.append(dotted_key)
                break
            node = node[part]
    return missing


def _check_placeholder_key(raw: dict) -> None:
    """Warn the user if the Gemini API key is still the placeholder value.

    Args:
        raw: The raw dictionary loaded from YAML.
    """
    key_value = raw.get("api", {}).get("gemini_key", "")
    if key_value == "PASTE_YOUR_KEY_HERE":
        print(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  ⚠  WARNING — Gemini API key not set!                      ║\n"
            "║                                                            ║\n"
            "║  Open config.yaml and replace PASTE_YOUR_KEY_HERE          ║\n"
            "║  with your real Gemini API key.                            ║\n"
            "║                                                            ║\n"
            "║  Get a free key → https://aistudio.google.com/apikey       ║\n"
            "╚══════════════════════════════════════════════════════════════╝\n"
        )


# ---------------------------------------------------------------------------
# Loader (called once, cached as module-level singleton)
# ---------------------------------------------------------------------------

def _load_config(config_path: str | None = None) -> ConfigNode:
    """Load, validate, and return the configuration as a ConfigNode.

    This function is called exactly once — the result is stored in the
    module-level ``config`` variable and imported everywhere else.

    Args:
        config_path: Optional explicit path for testing.

    Returns:
        A fully-validated ``ConfigNode`` object.
    """
    path = _resolve_path(config_path)

    # --- File existence ---------------------------------------------------
    if not path.exists():
        print(
            f"\n✖ Config file not found: {path}\n"
            f"  Create a config.yaml in the project root directory.\n"
            f"  See the README for the required structure.\n"
        )
        sys.exit(1)

    # --- YAML parsing -----------------------------------------------------
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw: dict = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        print(f"\n✖ Invalid YAML syntax in {path}:\n  {exc}\n")
        sys.exit(1)

    if raw is None or not isinstance(raw, dict):
        print(f"\n✖ Config file is empty or not a valid YAML mapping: {path}\n")
        sys.exit(1)

    # --- Required keys ----------------------------------------------------
    missing = _validate_required_keys(raw)
    if missing:
        print("\n✖ Missing required configuration keys:\n")
        for key in missing:
            print(f"  • {key}")
        print(f"\n  Add the missing keys to {path} and restart.\n")
        sys.exit(1)

    # --- Placeholder warning ----------------------------------------------
    _check_placeholder_key(raw)

    # --- Ensure data directory exists -------------------------------------
    project_root = path.parent
    data_dir = project_root / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # Non-critical — log warning once logger is available

    return ConfigNode(raw)


def reload_config(config_path: str | None = None) -> ConfigNode:
    """Force-reload the configuration from disk.

    Useful after the user edits config.yaml at runtime.

    Args:
        config_path: Optional explicit path override.

    Returns:
        A freshly-loaded ``ConfigNode`` object.
    """
    global config  # noqa: PLW0603
    config = _load_config(config_path)
    return config


# ---------------------------------------------------------------------------
# Module-level singleton — ``from utils.config_loader import config``
# ---------------------------------------------------------------------------

config: ConfigNode = _load_config()
