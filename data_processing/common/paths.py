# data_processing/common/paths.py
from pathlib import Path
from typing import Union

ROOT = Path(__file__).resolve().parents[2]  # project root (two levels up from this file)
DATA_ROOT = ROOT / "data"

def data_dir(gen: Union[int, str]) -> Path:
    """
    Return Path to the data directory for a generation.
    Example: data_dir(1) -> <repo>/data/gen1
    """
    return DATA_ROOT / f"gen{gen}"
