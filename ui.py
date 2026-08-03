import gradio as gr
import os
import database
from main import run_scan

# ── Helpers ───────────────────────────────────────────────────────────────────

def _person_label(pid: int) -> str:
    return f"Person {pid + 1}"

def _get_gallery(paths: list[str]) -> list[str]:
    return [p for p in paths if os.path.exists(p)]

# ── Handlers ──────────────────────────────────────────────────────────────────

def handle_scan(folder_path, progress=gr.Progress()):
    if not folder_path or not os.path.isdir(folder_path):
        return (
            "⚠️ Please enter a valid folder path.",
            gr.update(),
            gr.update(),
            gr.update(),
        )

    def progress_cb(stage, current, total):
        if total:
            progress(current / total, desc=stage)
        else:
            progress(0, desc=stage)

    try:
        stats = run_scan(folder_path, progress_cb=progress_cb)
    except Exception as e:
        return (f"❌ Scan failed: {e}", gr.update(), gr.update(), gr.update())

    summary = (
        f"✅ **{stats['new']} new photos indexed** · "
        f"📷 {stats['total']} total · "
        f"🏷️ {stats['categories']} categories · "
        f"👤 {stats['people']} people"
    )

    categories  = ["All"] + database.get_all_categories()
    person_ids  = database.get_all_person_ids()
    person_items = ["All"] + [_person_label(pid) for pid in person_ids]

    return (
        summary,
        gr.update(choices=categories,   value="All"),
        gr.update(choices=person_items, value="All"),
        _get_gallery(database.get_all_by_category("") or _all_photos()),
    )


def _all_photos() -> list[str]:
    paths = []
    for cat in database.get_all_categories():
        paths += database.get_all_by_category(cat)
    return _get_gallery(paths)


def on_category_select(category):
    if not category or category == "All":
        return _get_gallery(_all_photos())
    return _get_gallery(database.get_all_by_category(category))


def on_person_select(person_label):
    if not person_label or person_label == "All":
        return _get_gallery(_all_photos())
    pid = int(person_label.replace("Person ", "")) - 1
    return _get_gallery(database.get_all_by_person(pid))


# ── UI ────────────────────────────────────────────────────────────────────────

CSS = """
/* ── Layout ── */
#header { padding: 1.2rem 1.5rem 0.8rem; border-bottom: 1px solid #2d2a4a; background: #13111e; }
#app-title { font-size: 1.4rem; font-weight: 700; color: #4c1d95; margin: 0; }
#app-sub   { font-size: 0.85rem; color: #94a3b8; margin: 0; }
#sidebar   { border-right: 1px solid #e2e8f0; padding: 1.2rem 1rem;
             min-height: calc(100vh - 80px); background: #1e1b2e; }"
#main-area { padding: 1rem 1.2rem; }

/* ── Scan bar ── */
#scan-row  { display: flex; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.8rem; }
"#summary { font-size: 0.9rem; color: #a78bfa; background: #1e1b2e; border: 1px solid #2d2a4a; padding: 0.5rem 0.8rem; border-radius: 6px; margin-bottom: 0.8rem; }"
 
.gradio-container .gap { background: transparent !important; }
.gradio-radio { background: transparent !important; }

/* ── Sidebar items ── */
.sidebar-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
                 color: #94a3b8; text-transform: uppercase; margin: 1rem 0 0.4rem; }
#cat-list  .wrap { gap: 0.3rem !important; }
#cat-list  .svelte-1gfkn6j { border-radius: 6px !important; font-size: 0.85rem !important; }
#person-list .wrap { gap: 0.3rem !important; }
#person-list .svelte-1gfkn6j { border-radius: 6px !important; font-size: 0.85rem !important; }

/* ── Gallery ── */
#photo-grid { border-radius: 8px; overflow: hidden; }
"""


def build_ui():
    with gr.Blocks(
        title="Lumina · Photo Organizer",
        theme=gr.themes.Soft(
            primary_hue="violet",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter"),
        ),
        css=CSS,
    ) as app:

        # ── Header ────────────────────────────────────────────────────────────
        with gr.Row(elem_id="header"):
            with gr.Column(scale=1):
                gr.HTML("<p id='app-title'>Lumina</p><p id='app-sub'>Smart Photo Organizer</p>")
            with gr.Column(scale=4):
                with gr.Row(elem_id="scan-row"):
                    folder_input = gr.Textbox(
                        placeholder="Paste your photo folder path here…",
                        show_label=False,
                        scale=5,
                    )
                    scan_btn = gr.Button("🔍 Scan", variant="primary", scale=1, min_width=100)

        summary_box = gr.Markdown("", elem_id="summary")

        # ── Body: sidebar + grid ──────────────────────────────────────────────
        with gr.Row():

            # Sidebar
            with gr.Column(scale=1, elem_id="sidebar"):
                gr.HTML("<div class='sidebar-label'>Categories</div>")
                cat_radio = gr.Radio(
                    choices=["All"],
                    value="All",
                    show_label=False,
                    elem_id="cat-list",
                )

                gr.HTML("<div class='sidebar-label'>People</div>")
                person_radio = gr.Radio(
                    choices=["All"],
                    value="All",
                    show_label=False,
                    elem_id="person-list",
                )

            # Photo grid
            with gr.Column(scale=4, elem_id="main-area"):
                gallery = gr.Gallery(
                    show_label=False,
                    columns=4,
                    object_fit="scale-downgit",
                    height=620,
                    elem_id="photo-grid",
                )

        # ── Clear ────────────────────────────────────────────────────────────

        gr.HTML("<div class='sidebar-label'>Manage</div>")
        clear_btn = gr.Button("🗑️ Clear All", variant="stop", size="sm")
        clear_status = gr.Markdown("")

        def handle_clear():
            database.clear_all()
            return (
                "✅ Database cleared.",
                gr.update(choices=["All"], value="All"),
                gr.update(choices=["All"], value="All"),
                [],
            )

        clear_btn.click(
            handle_clear,
            outputs=[clear_status, cat_radio, person_radio, gallery],
        )

        # ── Wiring ────────────────────────────────────────────────────────────
        scan_btn.click(
            handle_scan,
            inputs=[folder_input],
            outputs=[summary_box, cat_radio, person_radio, gallery],
        )

        cat_radio.change(on_category_select, inputs=cat_radio, outputs=gallery)
        person_radio.change(on_person_select, inputs=person_radio, outputs=gallery)

    return app


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    database.init_db()
    app = build_ui()
    app.launch(inbrowser=True, allowed_paths=["/"])