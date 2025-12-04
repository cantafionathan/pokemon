# config.py

from pathlib import Path

# Default format if not set yet
_format = "gen1ou"

# Base project root
ROOT = Path(__file__).resolve().parent
BASE_DATA_DIR = ROOT / "data"

def set_format(fmt: str):
    global _format
    fmt = fmt.lower()
    if fmt not in {"gen1ou", "gen1ubers"}:
        raise ValueError("Format must be 'gen1ou' or 'gen1ubers'")
    _format = fmt

def DATA_DIR() -> Path:
    """Returns the effective data directory based on current format."""
    return BASE_DATA_DIR / _format

def get_format():
    return _format
