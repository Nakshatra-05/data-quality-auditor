from config import SCORE_WEIGHTS, GRADE_THRESHOLDS, PENALTY_MULTIPLIERS


def calculate_score(issues: dict, total_rows: int) -> dict:
    scores = {}

    # Missing values
    missing_count = issues["missing_values"]["count"]
    scores["missing_values"] = max(0, 100 - int(
        (missing_count / max(total_rows, 1)) * PENALTY_MULTIPLIERS["missing_values"]
    ))

    # Duplicates
    dupe_count = issues["duplicates"]["count"]
    scores["duplicates"] = max(0, 100 - int(
        (dupe_count / max(total_rows, 1)) * PENALTY_MULTIPLIERS["duplicates"]
    ))

    # Outliers
    total_outliers = sum(v["count"] for v in issues["outliers"].values())
    scores["outliers"] = max(0, 100 - int(
        (total_outliers / max(total_rows, 1)) * PENALTY_MULTIPLIERS["outliers"]
    ))

    # Invalid values
    total_invalid = sum(v["count"] for v in issues["invalid_values"].values())
    scores["invalid_values"] = max(0, 100 - int(
        (total_invalid / max(total_rows, 1)) * PENALTY_MULTIPLIERS["invalid_values"]
    ))

    # Type issues
    type_penalty = len(issues["type_issues"]) * PENALTY_MULTIPLIERS["type_issues"]
    scores["type_issues"] = max(0, 100 - type_penalty)

    # Weighted total using config weights
    total = sum(scores[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)

    return {
        "total": round(total),
        "breakdown": scores,
        "grade": _grade(total),
    }


def _grade(score: float) -> str:
    for label, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
        if score >= threshold:
            return label
    return "Critical"