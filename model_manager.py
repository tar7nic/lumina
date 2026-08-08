import os
import logging
from pathlib import Path
from config import MODEL_CACHE_DIR, CLIP_MODEL, CLIP_PRETRAINED

logger = logging.getLogger(__name__)

# ── Sentinel files ─────────────────────────────────────────────────────────────
# We write a small marker file once each model is confirmed ready,
# so we don't re-check / re-download on every launch.
_CLIP_READY_FLAG  = os.path.join(MODEL_CACHE_DIR, ".clip_ready")
_FACE_READY_FLAG  = os.path.join(MODEL_CACHE_DIR, ".face_ready")


def _ensure_dirs():
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)


# ── CLIP ───────────────────────────────────────────────────────────────────────

def is_clip_ready() -> bool:
    return os.path.exists(_CLIP_READY_FLAG)


def download_clip(progress_cb=None):
    _ensure_dirs()

    if progress_cb:
        progress_cb("Downloading scene-classification model (OpenCLIP) — this may take a minute…")

    try:
        import open_clip
        from huggingface_hub import hf_hub_download
        import torch

        # Manually download the weights file first
        logger.info("Pre-downloading OpenCLIP weights via huggingface_hub…")
        weights_path = hf_hub_download(
            repo_id="timm/vit_base_patch32_clip_224.openai",
            filename="open_clip_pytorch_model.bin",
            cache_dir=os.path.join(MODEL_CACHE_DIR, "huggingface", "hub"),
        )
        logger.info("Weights at: %s", weights_path)

        # Now load from the local file directly
        model, _, _ = open_clip.create_model_and_transforms(
            CLIP_MODEL,
            pretrained=weights_path,
        )
        Path(_CLIP_READY_FLAG).touch()
        logger.info("OpenCLIP ready.")
    except Exception as e:
        logger.error("Failed to download OpenCLIP: %s", e)
        raise RuntimeError(
            f"Could not download the scene-classification model.\n"
            f"Please check your internet connection and try again.\n\nDetail: {e}"
        )

# ── InsightFace ────────────────────────────────────────────────────────────────

def is_face_model_ready() -> bool:
    return os.path.exists(_FACE_READY_FLAG)


def download_face_model(progress_cb=None):
    """
    InsightFace downloads the buffalo_l pack automatically on first use.
    We set the home dir so it lands in our cache folder.
    """
    _ensure_dirs()

    os.environ["INSIGHTFACE_HOME"] = MODEL_CACHE_DIR

    if progress_cb:
        progress_cb("Downloading face-detection model (InsightFace buffalo_l)…")

    try:
        import insightface
        from insightface.app import FaceAnalysis
        logger.info("Loading InsightFace model…")
        app = FaceAnalysis(
            name="buffalo_l",
            root=MODEL_CACHE_DIR,
            providers=["CPUExecutionProvider"],
        )
        app.prepare(ctx_id=-1, det_size=(640, 640))
        Path(_FACE_READY_FLAG).touch()
        logger.info("InsightFace ready.")
    except Exception as e:
        logger.error("Failed to download InsightFace model: %s", e)
        raise RuntimeError(
            f"Could not download the face-detection model.\n"
            f"Please check your internet connection and try again.\n\nDetail: {e}"
        )


# ── Public API ─────────────────────────────────────────────────────────────────

def check_and_download_models(progress_cb=None, force=False):
    """
    Called once at app startup. Downloads any missing models.
    progress_cb(message: str) is an optional callable used to push
    status text to the UI while downloading.
    force=True re-downloads even if sentinel flags exist.

    Returns a dict describing what was done:
        {"clip": "ready"|"downloaded"|"failed",
         "face": "ready"|"downloaded"|"failed"}
    """
    _ensure_dirs()
    if force:
        reset_model_cache()
    result = {}

    # ── CLIP ──
    if is_clip_ready():
        logger.info("OpenCLIP already cached — skipping download.")
        result["clip"] = "ready"
    else:
        try:
            download_clip(progress_cb)
            result["clip"] = "downloaded"
        except RuntimeError:
            result["clip"] = "failed"

    # ── Face ──
    if is_face_model_ready():
        logger.info("InsightFace already cached — skipping download.")
        result["face"] = "ready"
    else:
        try:
            download_face_model(progress_cb)
            result["face"] = "downloaded"
        except RuntimeError:
            result["face"] = "failed"

    return result


def models_are_ready() -> bool:
    """Quick boolean — True only if both models are cached and ready."""
    return is_clip_ready() and is_face_model_ready()


def reset_model_cache():
    """
    Delete sentinel flags so models are re-downloaded on next launch.
    Useful for a 'reinstall models' button in settings.
    """
    for flag in (_CLIP_READY_FLAG, _FACE_READY_FLAG):
        if os.path.exists(flag):
            os.remove(flag)
            logger.info("Removed flag: %s", flag)