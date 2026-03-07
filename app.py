#!/usr/bin/env python3
"""
Borrower Metrics — Flask web app.
Serves generated reports and lets you generate new ones from built-in samples.

Run:  python app.py
Then open http://localhost:5000
"""
import os
import re
from pathlib import Path

from flask import (
    Flask, render_template, redirect, url_for,
    send_from_directory, flash, abort,
)

from borrower_metrics.generate import generate_reports
from borrower_metrics.sample_data import ALL_SAMPLES

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "borrower-metrics-dev-key")

# ── Badge classes for the UI ───────────────────────────────────────────────
BADGE_MAP = {
    "charter_school": "charter",
    "fqhc":           "fqhc",
    "early_care":     "early",
    "nonprofit":      "nonprofit",
}
TYPE_LABEL = {
    "charter_school": "Charter School",
    "fqhc":           "FQHC",
    "early_care":     "Early Care",
    "nonprofit":      "Nonprofit",
}


def _sample_meta():
    return {
        key: {
            "name":        profile.name,
            "location":    profile.location,
            "year_founded":profile.year_founded,
            "type_label":  TYPE_LABEL.get(key, key),
            "badge":       BADGE_MAP.get(key, "nonprofit"),
        }
        for key, profile in ALL_SAMPLES.items()
    }


def _report_pairs():
    """
    Return list of (display_name, pdf_filename_or_None, xlsx_filename_or_None)
    grouped by stem.
    """
    files = list(OUTPUT_DIR.iterdir())
    stems = sorted(
        {f.stem for f in files if f.suffix in (".pdf", ".xlsx")},
        key=lambda s: s.lower(),
    )
    pairs = []
    for stem in stems:
        display = stem.replace("_", " ")
        pdf  = stem + ".pdf"  if (OUTPUT_DIR / (stem + ".pdf")).exists()  else None
        xlsx = stem + ".xlsx" if (OUTPUT_DIR / (stem + ".xlsx")).exists() else None
        pairs.append((display, pdf, xlsx))
    return pairs


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return render_template(
        "index.html",
        samples=_sample_meta(),
        report_pairs=_report_pairs(),
    )


@app.post("/generate/<sample_key>")
def generate(sample_key):
    if sample_key not in ALL_SAMPLES:
        abort(404)
    profile = ALL_SAMPLES[sample_key]
    try:
        generate_reports(profile, output_dir=str(OUTPUT_DIR))
        flash(f"Reports generated for {profile.name}.", "ok")
    except Exception as exc:
        flash(f"Generation failed: {exc}", "error")
    return redirect(url_for("index"))


@app.get("/download/<filename>")
def download(filename):
    # Prevent path traversal
    if "/" in filename or ".." in filename:
        abort(400)
    safe = re.sub(r"[^A-Za-z0-9_\-. ]", "", filename)
    if safe != filename:
        abort(400)
    return send_from_directory(str(OUTPUT_DIR), filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
