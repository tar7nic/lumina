import os
import logging
import torch
import open_clip
from PIL import Image
from config import (
    CATEGORIES, CLIP_MODEL, CLIP_PRETRAINED,
    CLIP_BATCH_SIZE, MODEL_CACHE_DIR
)

logger = logging.getLogger(__name__)

# Module-level singletons — loaded once, reused across calls
_model      = None
_preprocess = None
_tokenizer  = None
_text_features = None
_device     = None


def _get_weights_path() -> str:
    """Find the locally cached OpenCLIP weights file."""
    hub_dir = os.path.join(MODEL_CACHE_DIR, "huggingface", "hub")
    for root, _, files in os.walk(hub_dir):
        for f in files:
            if f == "open_clip_pytorch_model.bin":
                return os.path.join(root, f)
    raise FileNotFoundError(
        "OpenCLIP weights not found in cache. Run model_manager.check_and_download_models() first."
    )


def load_model():
    """Load OpenCLIP model and pre-compute text features for all categories."""
    global _model, _preprocess, _tokenizer, _text_features, _device

    if _model is not None:
        return  # already loaded

    _device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading OpenCLIP on %s", _device)

    weights_path = _get_weights_path()
    _model, _, _preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL, pretrained=weights_path
    )
    _model = _model.to(_device).eval()
    _tokenizer = open_clip.get_tokenizer(CLIP_MODEL)

    # Pre-compute text embeddings for all category labels (done once)
    prompts = [f"a photo of {c}" for c in CATEGORIES]
    tokens  = _tokenizer(prompts).to(_device)
    with torch.no_grad():
        text_feats = _model.encode_text(tokens)
        text_feats /= text_feats.norm(dim=-1, keepdim=True)
    _text_features = text_feats

    logger.info("OpenCLIP loaded. %d categories ready.", len(CATEGORIES))


def classify_image(image_path: str) -> tuple[str, float]:
    """
    Classify a single image.
    Returns (category_label, confidence_score).
    Falls back to ("other", 0.0) on any error.
    """
    if _model is None:
        load_model()

    try:
        image = _preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(_device)
        with torch.no_grad():
            img_feats = _model.encode_image(image)
            img_feats /= img_feats.norm(dim=-1, keepdim=True)
            probs = (img_feats @ _text_features.T).softmax(dim=-1)[0]
        idx        = probs.argmax().item()
        confidence = probs[idx].item()
        return CATEGORIES[idx], round(confidence, 4)
    except Exception as e:
        logger.warning("classify_image failed for %s: %s", image_path, e)
        return "other", 0.0


def classify_batch(image_paths: list[str], batch_size: int = CLIP_BATCH_SIZE,
                   progress_cb=None) -> list[tuple[str, float]]:
    """
    Classify a list of images in batches.
    Returns a list of (category, confidence) tuples in the same order.
    progress_cb(current, total) is called after each batch.
    """
    if _model is None:
        load_model()

    results = []
    total   = len(image_paths)

    for start in range(0, total, batch_size):
        batch_paths = image_paths[start: start + batch_size]
        images = []

        for p in batch_paths:
            try:
                img = _preprocess(Image.open(p).convert("RGB"))
                images.append(img)
            except Exception as e:
                logger.warning("Skipping unreadable image %s: %s", p, e)
                images.append(None)

        # Build tensor from valid images only, track positions of failed ones
        valid_imgs   = [img for img in images if img is not None]
        valid_idxs   = [i for i, img in enumerate(images) if img is not None]

        batch_results = [("other", 0.0)] * len(batch_paths)

        if valid_imgs:
            tensor = torch.stack(valid_imgs).to(_device)
            with torch.no_grad():
                img_feats = _model.encode_image(tensor)
                img_feats /= img_feats.norm(dim=-1, keepdim=True)
                probs = (img_feats @ _text_features.T).softmax(dim=-1)

            for pos, orig_idx in enumerate(valid_idxs):
                idx        = probs[pos].argmax().item()
                confidence = probs[pos][idx].item()
                batch_results[orig_idx] = (CATEGORIES[idx], round(confidence, 4))

        results.extend(batch_results)

        if progress_cb:
            progress_cb(min(start + batch_size, total), total)

    return results