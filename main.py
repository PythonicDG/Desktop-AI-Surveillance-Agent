"""
DeskMate — Main Entry Point
============================
Launches the DeskMate AI desktop surveillance agent.

Usage:
    python main.py
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so package imports work when
# running ``python main.py`` directly from the project directory.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Start DeskMate — load config and print the startup banner."""
    try:
        # Config is loaded (and validated) at import time via the singleton.
        from utils.config_loader import config  # noqa: F811

        # Ensure the data directory exists
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Startup banner
        print(
            f"\n"
            f"  ╔══════════════════════════════════════╗\n"
            f"  ║   🤖 DeskMate v{VERSION}               ║\n"
            f"  ║   Config loaded. Ready to roll.      ║\n"
            f"  ╚══════════════════════════════════════╝\n"
        )

        # Quick sanity echo
        print(f"  Model        : {config.api.primary_model}")
        print(f"  Fallback     : {config.api.fallback_model}")
        print(f"  Hotkey       : {config.hotkeys.trigger}")
        print(f"  Theme        : {config.ui.theme}")
        print(f"  Privacy      : {'ON' if config.privacy.enabled else 'OFF'}")
        print(f"  Timeline     : {'ON' if config.features.timeline_enabled else 'OFF'}")
        print(f"  Debug        : {'ON' if config.get('debug', False) else 'OFF'}")
        print()

        print("DeskMate v1.0 starting... Config loaded.")

    except SystemExit:
        # Config loader calls sys.exit on validation failure — let it propagate
        raise
    except Exception as exc:
        print(f"\n✖ Unexpected error during startup: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
