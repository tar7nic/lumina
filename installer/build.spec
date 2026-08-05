import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_all

block_cipher = None

PACKAGES = [
    "gradio", "gradio_client", "safehttpx", "groovy", "httpx",
    "open_clip", "insightface", "sklearn", "timm", "huggingface_hub",
    "tokenizers",
]

datas, binaries, hiddenimports = [], [], []

for pkg in PACKAGES:
    try:
        d, b, h = collect_all(pkg)
        datas         += d
        binaries      += b
        hiddenimports += h
    except Exception:
        pass

binaries += collect_dynamic_libs("onnxruntime")

hiddenimports += [
    "database", "scanner", "categorizer", "face_pipeline",
    "model_manager", "config", "main",
    "sklearn.cluster", "sklearn.neighbors",
    "sklearn.utils._cython_blas", "sklearn.utils._weight_vector",
    "cv2", "faiss", "tqdm",
]

a = Analysis(
    ["../ui.py"],
    pathex=[".."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=["installer/hook_uvicorn.py"],
    excludes=["matplotlib", "notebook", "ipython", "pytest"],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Lumina",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="../assets/icon.ico" if sys.platform == "win32" else None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[], name="Lumina",
)
