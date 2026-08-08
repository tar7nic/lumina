import sqlite3
import numpy as np
from datetime import datetime
from config import DB_PATH
import os

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _embedding_to_blob(embedding: np.ndarray) -> bytes | None:
    if embedding is None:
        return None
    return embedding.astype(np.float32).tobytes()

def _blob_to_embedding(blob: bytes) -> np.ndarray | None:
    if blob is None:
        return None
    return np.frombuffer(blob, dtype=np.float32)

# ── schema ────────────────────────────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist yet."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                path                TEXT    UNIQUE NOT NULL,
                category            TEXT,
                category_confidence REAL,
                person_id           INTEGER,
                face_embedding      BLOB,
                indexed_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category  ON images(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_person_id ON images(person_id)")
        conn.commit()

# ── writes ────────────────────────────────────────────────────────────────────

def insert_image(path: str, category: str = None, confidence: float = None,
                 person_id: int = None, embedding: np.ndarray = None):
    """Insert a new image record. Silently ignores duplicates."""
    blob = _embedding_to_blob(embedding)
    with _get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO images
                (path, category, category_confidence, person_id, face_embedding, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (path, category, confidence, person_id, blob, datetime.utcnow()))
        conn.commit()

def update_image_category(path: str, category: str, confidence: float):
    """Update category info for an existing record."""
    with _get_conn() as conn:
        conn.execute("""
            UPDATE images SET category = ?, category_confidence = ? WHERE path = ?
        """, (category, confidence, path))
        conn.commit()

def update_image_embedding(path: str, embedding: np.ndarray):
    """Store face embedding for an existing record."""
    blob = _embedding_to_blob(embedding)
    with _get_conn() as conn:
        conn.execute("UPDATE images SET face_embedding = ? WHERE path = ?", (blob, path))
        conn.commit()

def update_person_ids(mapping: dict[str, int]):
    """
    Bulk-update person_id after clustering.
    mapping: { image_path: person_id, ... }
    person_id = -1 means unknown / no cluster.
    """
    with _get_conn() as conn:
        conn.executemany(
            "UPDATE images SET person_id = ? WHERE path = ?",
            [(pid, path) for path, pid in mapping.items()]
        )
        conn.commit()

def clear_all():
    """Wipe all records (full rescan)."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM images")
        conn.commit()

# ── reads ─────────────────────────────────────────────────────────────────────

def image_exists(path: str) -> bool:
    with _get_conn() as conn:
        row = conn.execute("SELECT 1 FROM images WHERE path = ?", (path,)).fetchone()
    return row is not None

def get_all_by_category(category: str) -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT path FROM images WHERE category = ? ORDER BY path", (category,)
        ).fetchall()
    return [r["path"] for r in rows]

def get_all_by_person(person_id: int) -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT path FROM images WHERE person_id = ? ORDER BY path", (person_id,)
        ).fetchall()
    return [r["path"] for r in rows]

def get_all_categories() -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM images WHERE category IS NOT NULL ORDER BY category"
        ).fetchall()
    return [r["category"] for r in rows]

def get_all_person_ids() -> list[int]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT person_id FROM images WHERE person_id IS NOT NULL AND person_id != -1"
        ).fetchall()
    return [r["person_id"] for r in rows]

def get_all_embeddings() -> tuple[list[str], list[np.ndarray]]:
    """
    Return (paths, embeddings) for all images that have a face embedding.
    Used to feed into DBSCAN clustering after a full scan.
    """
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT path, face_embedding FROM images WHERE face_embedding IS NOT NULL"
        ).fetchall()
    paths, embeddings = [], []
    for r in rows:
        emb = _blob_to_embedding(r["face_embedding"])
        if emb is not None:
            paths.append(r["path"])
            embeddings.append(emb)
    return paths, embeddings

def get_stats() -> dict:
    """Quick summary stats for the UI."""
    with _get_conn() as conn:
        total     = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        n_cats    = conn.execute("SELECT COUNT(DISTINCT category) FROM images WHERE category IS NOT NULL").fetchone()[0]
        n_people  = conn.execute(
            "SELECT COUNT(DISTINCT person_id) FROM images WHERE person_id IS NOT NULL AND person_id != -1"
        ).fetchone()[0]
    return {"total": total, "categories": n_cats, "people": n_people}