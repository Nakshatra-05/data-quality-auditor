import os
import json
from datetime import datetime


HISTORY_DIR = "history"


def save_run(filename: str, score: dict, issues: dict) -> str:
    """Save a quality scan result to the history folder as a JSON file."""

    os.makedirs(HISTORY_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name  = filename.replace(".csv", "").replace(" ", "_")
    filepath   = os.path.join(HISTORY_DIR, f"{safe_name}_{timestamp}.json")

    record = {
        "filename":   filename,
        "scanned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": {
            "total":     score["total"],
            "grade":     score["grade"],
            "breakdown": score["breakdown"],
        },
        "summary": {
            "missing_cells":  issues["missing_values"]["count"],
            "duplicates":     issues["duplicates"]["count"],
            "outlier_cols":   list(issues["outliers"].keys()),
            "invalid_checks": list(issues["invalid_values"].keys()),
            "type_issues":    list(issues["type_issues"].keys()),
        },
    }

    with open(filepath, "w") as f:
        json.dump(record, f, indent=2)

    return filepath


def load_history(filename_filter: str = None) -> list:
    """Load all past scan records, optionally filtered by filename."""

    if not os.path.exists(HISTORY_DIR):
        return []

    records = []
    for fname in sorted(os.listdir(HISTORY_DIR)):
        if not fname.endswith(".json"):
            continue
        if filename_filter and filename_filter.replace(".csv", "") not in fname:
            continue
        with open(os.path.join(HISTORY_DIR, fname)) as f:
            try:
                records.append(json.load(f))
            except json.JSONDecodeError:
                continue

    return records


def get_trend(records: list) -> dict:
    """Extract score trend data from history records for charting."""

    if not records:
        return {"dates": [], "scores": [], "grades": []}

    dates  = [r["scanned_at"] for r in records]
    scores = [r["score"]["total"] for r in records]
    grades = [r["score"]["grade"] for r in records]

    return {
        "dates":  dates,
        "scores": scores,
        "grades": grades,
    }