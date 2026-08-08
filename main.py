import logging
import database
import scanner
import categorizer
import face_pipeline
from model_manager import check_and_download_models, models_are_ready

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_scan(folder_path: str, progress_cb=None) -> dict:
    """
    Full pipeline:
      1. Init DB
      2. Ensure models are ready
      3. Scan folder for new images
      4. For each image: classify scene + extract face embedding → save to DB
      5. Run face clustering → update person_ids in DB
      6. Return summary stats

    progress_cb(stage: str, current: int, total: int) — optional UI hook.
    """

    def _progress(stage, current=0, total=0):
        if progress_cb:
            progress_cb(stage, current, total)
        logger.info("[%s] %d / %d", stage, current, total)

    # ── Step 1: DB ────────────────────────────────────────────────────────────
    _progress("Initialising database", 0, 0)
    database.init_db()

    # ── Step 2: Models ────────────────────────────────────────────────────────
    if not models_are_ready():
        _progress("Downloading models — please wait…", 0, 0)
        result = check_and_download_models(
            progress_cb=lambda msg: _progress(msg, 0, 0)
        )
        if result.get("clip") == "failed" or result.get("face") == "failed":
            raise RuntimeError(
                "One or more models failed to download. "
                "Check your internet connection and restart the app."
            )

    # ── Step 3: Load models into memory ──────────────────────────────────────
    _progress("Loading models into memory…", 0, 0)
    categorizer.load_model()
    face_pipeline.load_model()

    # ── Step 4: Scan folder ───────────────────────────────────────────────────
    _progress("Scanning folder…", 0, 0)
    new_paths, total_found = scanner.scan_new(folder_path)

    if not new_paths:
        stats = database.get_stats()
        stats["skipped"] = total_found
        stats["new"]     = 0
        _progress("Nothing new to index.", 0, 0)
        return stats

    _progress("Indexing images", 0, len(new_paths))

    # ── Step 5: Per-image processing ─────────────────────────────────────────
    # Pre-insert all new paths as empty records so we can update them
    for path in new_paths:
        database.insert_image(path)

    # Scene classification — batched
    def clip_progress(current, total):
        _progress("Classifying scenes", current, total)

    categories = categorizer.classify_batch(
        new_paths,
        progress_cb=clip_progress,
    )
    for path, (category, confidence) in zip(new_paths, categories):
        database.update_image_category(path, category, confidence)

    # Face embeddings — per image
    def face_progress(current, total):
        _progress("Extracting faces", current, total)

    embeddings_map = face_pipeline.get_face_embeddings_batch(
        new_paths,
        progress_cb=face_progress,
    )
    for path, embedding in embeddings_map.items():
        database.update_image_embedding(path, embedding)

    # ── Step 6: Cluster all faces in DB ──────────────────────────────────────
    _progress("Clustering faces…", 0, 0)
    cluster_stats = face_pipeline.run_full_clustering(database)

    # ── Step 7: Return summary ────────────────────────────────────────────────
    stats = database.get_stats()
    stats["new"]           = len(new_paths)
    stats["skipped"]       = total_found - len(new_paths)
    stats["people"]        = cluster_stats["people"]
    stats["unrecognised"]  = cluster_stats["unrecognised"]

    _progress("Done!", stats["new"], stats["new"])
    return stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <folder_path>")
        sys.exit(1)

    folder = sys.argv[1]

    def cli_progress(stage, current, total):
        if total:
            print(f"  [{stage}] {current}/{total}")
        else:
            print(f"  {stage}")

    print(f"\nScanning: {folder}\n")
    result = run_scan(folder, progress_cb=cli_progress)
    print("\n── Results ──────────────────────────────")
    print(f"  Total in DB : {result['total']}")
    print(f"  New indexed : {result['new']}")
    print(f"  Skipped     : {result['skipped']}")
    print(f"  Categories  : {result['categories']}")
    print(f"  People      : {result['people']}")
    print(f"  Unrecognised: {result['unrecognised']}")