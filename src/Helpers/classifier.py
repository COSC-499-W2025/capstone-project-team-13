import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Settings.config import EXT_SUPERTYPES


def supertype_from_extension(file_path: str) -> str | None:
    _, ext = os.path.splitext(file_path)
    return EXT_SUPERTYPES.get(ext.lower())
