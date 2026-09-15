from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_page_is_a_self_contained_static_lab():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'href="web/style.css"' in html
    assert 'type="module" src="web/app.mjs"' in html
    assert "https://" not in html
    assert "http://" not in html


def test_live_lab_exposes_controls_metrics_and_canvases():
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    for required_id in (
        "policy",
        "seed",
        "threshold",
        "run-toggle",
        "step-once",
        "reset-world",
        "receiver-rmse",
        "sender-rmse",
        "message-rate",
        "detector-f1",
        "shared-alignment",
        "trace-canvas",
        "frontier-canvas",
        "world-status",
    ):
        assert f'id="{required_id}"' in html

    assert "V5 LIVE DEVELOPMENT LAB" in html
    assert "shared subspace" in html.lower()


def test_browser_app_and_styles_are_repo_local_files():
    assert (ROOT / "web" / "style.css").is_file()
    assert (ROOT / "web" / "app.mjs").is_file()
    assert (ROOT / "web" / "vector_live.mjs").is_file()

    app = (ROOT / "web" / "app.mjs").read_text(encoding="utf-8")
    assert "./vector_live.mjs" in app
    assert "createLiveVectorMachine" in app
