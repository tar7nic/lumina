import os
import logging
import numpy as np
from config import MODEL_CACHE_DIR, DBSCAN_EPS, DBSCAN_MIN_SAMPLES

logger = logging.getLogger(__name__)

# Module-level singleton
_face_app = None


# ── Model ─────────────────────────────────────────────────────────────────────

def load_model():
    """Load InsightFace buffalo_l model (once)."""
    global _face_app
    if _face_app is not None:
        return

    os.environ["INSIGHTFACE_HOME"] = MODEL_CACHE_DIR

    from insightface.app import FaceAnalysis
    logger.info("Loading InsightFace model…")
    _face_app = FaceAnalysis(
        name="buffalo_l",
        root=MODEL_CACHE_DIR,
        providers=["CPUExecutionProvider"],
    )
    _face_app.prepare(ctx_id=-1, det_size=(640, 640))
    logger.info("InsightFace ready.")


# ── Embedding extraction ───────────────────────────────────────────────────────

def get_face_embedding(image_path: str) -> np.ndarray | None:
    """
    Detect faces in one image and return the embedding of the
    largest (most prominent) face as a 512-D numpy array.
    Returns None if no face is detected or image is unreadable.
    """
    if _face_app is None:
        load_model()

    try:
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            logger.warning("Could not read image: %s", image_path)
            return None

        faces = _face_app.get(img)
        if not faces:
            return None

        # Pick the largest face by bounding-box area
        largest = max(faces, key=lambda f: (
            (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
        ))
        return largest.embedding.astype(np.float32)

    except Exception as e:
        logger.warning("Face extraction failed for %s: %s", image_path, e)
        return None


def get_face_embeddings_batch(image_paths: list[str],
                              progress_cb=None) -> dict[str, np.ndarray]:
    """
    Extract face embeddings for a list of images.
    Returns {path: embedding} for images where a face was found.
    Images with no face are omitted from the result.
    progress_cb(current, total) called after each image.
    """
    if _face_app is None:
        load_model()

    results = {}
    total   = len(image_paths)

    for i, path in enumerate(image_paths):
        emb = get_face_embedding(path)
        if emb is not None:
            results[path] = emb
        if progress_cb:
            progress_cb(i + 1, total)

    logger.info("Face embeddings extracted: %d / %d images had faces", len(results), total)
    return results


# ── Clustering ────────────────────────────────────────────────────────────────

def cluster_faces(paths: list[str],
                  embeddings: list[np.ndarray]) -> dict[str, int]:
    """
    Run DBSCAN clustering on face embeddings.

    Args:
        paths:      list of image paths (same order as embeddings)
        embeddings: list of 512-D numpy arrays

    Returns:
        {image_path: person_id}
        person_id = -1 means unrecognised / singleton (no cluster).
        person_id >= 0 means a named cluster (Person 0, Person 1, …).
    """
    if not embeddings:
        logger.info("No embeddings to cluster.")
        return {}

    from sklearn.cluster import DBSCAN

    X = np.array(embeddings)

    # Normalise for cosine similarity via euclidean DBSCAN
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1          # avoid divide-by-zero
    X_norm = X / norms

    clustering = DBSCAN(
        eps=DBSCAN_EPS,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric="euclidean",        # cosine ≈ euclidean on unit vectors
    )
    labels = clustering.fit_predict(X_norm)

    mapping = {path: int(label) for path, label in zip(paths, labels)}

    n_people  = len(set(labels) - {-1})
    n_unknown = sum(1 for l in labels if l == -1)
    logger.info("Clustering done: %d people found, %d unrecognised faces", n_people, n_unknown)

    return mapping


def run_full_clustering(db) -> dict:
    """
    Convenience function called from main pipeline:
    1. Load all embeddings from DB
    2. Run DBSCAN
    3. Push person_id updates back to DB
    Returns clustering stats.
    """
    paths, embeddings = db.get_all_embeddings()

    if not paths:
        return {"people": 0, "unrecognised": 0}

    mapping  = cluster_faces(paths, embeddings)
    db.update_person_ids(mapping)

    n_people  = len(set(mapping.values()) - {-1})
    n_unknown = sum(1 for v in mapping.values() if v == -1)
    return {"people": n_people, "unrecognised": n_unknown}