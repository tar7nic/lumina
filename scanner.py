import os
from pathlib import Path
from config import IMAGE_EXTENSIONS
import database


def scan_folder(folder_path: str) -> list[str]:
    """
    Recursively walk folder_path and return absolute paths
    of all supported image files.
    """
    found = []
    for root, _, files in os.walk(folder_path):
        for fname in files:
            if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                found.append(os.path.abspath(os.path.join(root, fname)))
    return sorted(found)


def filter_new_images(all_paths: list[str]) -> list[str]:
    """
    Exclude images that are already in the DB (incremental scan).
    Returns only paths not yet indexed.
    """
    return [p for p in all_paths if not database.image_exists(p)]


def scan_new(folder_path: str) -> tuple[list[str], int]:
    """
    Convenience wrapper — scans folder and filters already-indexed images.
    Returns (new_paths, total_found).
    """
    all_paths = scan_folder(folder_path)
    new_paths = filter_new_images(all_paths)
    return new_paths, len(all_paths)