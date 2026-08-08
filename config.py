import os

APP_NAME = "Smart Photo Organizer"
VERSION  = "1.0.0"

# ── Paths ─────────────────────────────────────────────────────────────────────
HOME_DIR       = os.path.expanduser("~")
APP_DATA_DIR   = os.path.join(HOME_DIR, ".photo_organizer")
DB_PATH        = os.path.join(APP_DATA_DIR, "index.db")
MODEL_CACHE_DIR= os.path.join(APP_DATA_DIR, "models")

# ── Scene categories (used by OpenCLIP zero-shot) ─────────────────────────────
CATEGORIES = [
    "food and drinks",
    "nature and scenery",
    "people and portraits",
    "documents and screenshots",
    "animals and pets",
    "travel and architecture",
    "events and celebrations",
    "sports and fitness",
    "selfie",
    "other",
]

# ── CLIP model ────────────────────────────────────────────────────────────────
CLIP_MODEL      = "ViT-B-32"
CLIP_PRETRAINED = "openai"
CLIP_BATCH_SIZE = 32

# ── Face clustering ───────────────────────────────────────────────────────────
DBSCAN_EPS         = 0.4
DBSCAN_MIN_SAMPLES = 2

# ── Supported image extensions ────────────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}