import pandas as pd
from datetime import datetime


def detect_schema_drift(df_old: pd.DataFrame, df_new: pd.DataFrame) -> dict:
    """Compare two dataframes and detect any schema changes."""

    old_cols = set(df_old.columns)
    new_cols = set(df_new.columns)

    added_cols    = new_cols - old_cols
    removed_cols  = old_cols - new_cols
    common_cols   = old_cols & new_cols

    # Check for data type changes in common columns
    type_changes = {}
    for col in common_cols:
        old_type = str(df_old[col].dtype)
        new_type = str(df_new[col].dtype)
        if old_type != new_type:
            type_changes[col] = {
                "old_type": old_type,
                "new_type": new_type,
            }

    # Check for row count changes
    row_diff = len(df_new) - len(df_old)

    # Check for null rate changes in common columns
    null_rate_changes = {}
    for col in common_cols:
        old_null_rate = round(df_old[col].isnull().mean() * 100, 2)
        new_null_rate = round(df_new[col].isnull().mean() * 100, 2)
        diff = round(new_null_rate - old_null_rate, 2)
        if abs(diff) >= 5:  # flag if null rate changed by 5% or more
            null_rate_changes[col] = {
                "old_null_rate": old_null_rate,
                "new_null_rate": new_null_rate,
                "change": diff,
            }

    # Overall drift detected?
    drift_detected = bool(
        added_cols or removed_cols or type_changes or null_rate_changes
    )

    return {
        "drift_detected":    drift_detected,
        "added_columns":     list(added_cols),
        "removed_columns":   list(removed_cols),
        "type_changes":      type_changes,
        "null_rate_changes": null_rate_changes,
        "row_count": {
            "old": len(df_old),
            "new": len(df_new),
            "diff": row_diff,
        },
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def summarise_drift(drift: dict) -> str:
    """Return a human-readable one-line summary of drift findings."""
    if not drift["drift_detected"]:
        return "No schema drift detected. Dataset structure is consistent."

    parts = []
    if drift["added_columns"]:
        parts.append(f"{len(drift['added_columns'])} column(s) added: {drift['added_columns']}")
    if drift["removed_columns"]:
        parts.append(f"{len(drift['removed_columns'])} column(s) removed: {drift['removed_columns']}")
    if drift["type_changes"]:
        parts.append(f"{len(drift['type_changes'])} column(s) changed type")
    if drift["null_rate_changes"]:
        parts.append(f"{len(drift['null_rate_changes'])} column(s) have significant null rate changes")

    return " | ".join(parts)