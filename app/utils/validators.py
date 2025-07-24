from pathlib import Path
from typing import Set, Optional
try:
    import magic
except ImportError:
    magic = None

def validate_file_extension(filename: str, allowed_extensions: Set[str]) -> bool:
    """Check if the file’s suffix is among allowed extensions."""
    return Path(filename).suffix.lower() in allowed_extensions

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Ensure file size does not exceed max_size (in bytes)."""
    return file_size <= max_size

def validate_file_content(filepath: str) -> bool:
    """
    If python-magic is available, check the file’s MIME type against known spreadsheet mimes.
    Otherwise, skip this check.
    """
    if magic is None:
        return True

    try:
        mime = magic.from_file(filepath, mime=True)
        allowed = {
            "text/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        return mime in allowed
    except Exception:
        return True
