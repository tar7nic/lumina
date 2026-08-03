<div align="center">

# 🖼️ Lumina
### Smart Photo Organizer

**Scan a folder. Let AI do the rest.**

Lumina automatically organizes your photos by scene and groups them by the people in them — no manual sorting, no cloud uploads, no subscriptions. Everything runs locally on your machine.

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## ✨ What it does

- 🏷️ **Scene Classification** — automatically sorts photos into categories like Food, Nature, Travel, Documents, Events, and more
- 👤 **Face Clustering** — groups photos by the people in them, with no labeling needed
- ⚡ **Incremental Scanning** — rescan a folder and only new photos get processed
- 🔒 **100% Offline** — your photos never leave your machine
- 🖥️ **Simple UI** — clean browser-based interface, no tech skills needed

---

## 📸 Categories detected

| Category | Category | Category |
|---|---|---|
| 🍕 Food & Drinks | 🌿 Nature & Scenery | 🤳 Selfie |
| 📄 Documents & Screenshots | 🐾 Animals & Pets | 🏛️ Travel & Architecture |
| 🎉 Events & Celebrations | 🏋️ Sports & Fitness | 👥 People & Portraits |

---

## 🛠️ Tech Stack

| Component | Library |
|---|---|
| Scene Classification | OpenCLIP (zero-shot, no training needed) |
| Face Detection | InsightFace `buffalo_l` |
| Face Clustering | DBSCAN (scikit-learn) |
| UI | Gradio |
| Database | SQLite |
| Packaging | PyInstaller + Inno Setup |

---

## 🚀 Getting Started

### Option A — Use the installer (Windows)
1. Download `LuminaSetup.exe` from [Releases](../../releases)
2. Run the installer and follow the steps
3. Launch **Lumina** from your desktop
4. On first launch, AI models will download automatically (~1–2 GB, internet required)
5. Paste your photo folder path → hit **Scan** → done!

### Option B — Run from source

```bash
# Clone the repo
git clone https://github.com/yourusername/lumina.git
cd lumina

# Create and activate a virtual environment (Python 3.10)
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Launch
python ui.py
```

---

## 📁 Project Structure

```
lumina/
├── ui.py               # Gradio interface
├── main.py             # Pipeline orchestrator
├── scanner.py          # Folder walker
├── categorizer.py      # OpenCLIP scene classifier
├── face_pipeline.py    # Face detection + clustering
├── database.py         # SQLite layer
├── model_manager.py    # First-run model downloads
├── config.py           # Constants and settings
├── requirements.txt
├── installer/
│   ├── build.spec      # PyInstaller spec
│   └── setup.iss       # Inno Setup config
└── .github/
    └── workflows/
        └── build.yml   # Auto-build on push
```

---

## 🔧 How it works

```
📁 Your Photo Folder
        │
        ▼
  🔍 Scan & filter new images
        │
        ├──▶ 🏷️ OpenCLIP classifies each photo by scene
        │         (zero-shot: no training, just text prompts)
        │
        └──▶ 👤 InsightFace extracts face embeddings
                  │
                  ▼
             DBSCAN clusters similar faces → Person 1, Person 2…
                  │
                  ▼
             💾 Results saved to local SQLite DB
                  │
                  ▼
             🖥️ Browse by Category or Person in the UI
```

---

## 🏗️ Building the installer

```bash
# Install PyInstaller
pip install pyinstaller

# Build the exe
pyinstaller installer/build.spec --distpath dist --workpath build --noconfirm

# Then open Inno Setup → load installer/setup.iss → Compile
# Output: installer/Output/LuminaSetup.exe
```

Or just push to `main` — GitHub Actions builds it automatically.

---

## 📋 Requirements

- Windows 10 or 11
- ~2 GB free disk space (for AI models, downloaded on first run)
- Internet connection on first launch only

---

## 🤝 Contributing

Pull requests are welcome! If you find a bug or want to suggest a feature, open an issue.

---

<div align="center">

Built with ❤️ using Python, OpenCLIP, and InsightFace

</div>
