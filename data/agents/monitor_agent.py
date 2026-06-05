def run(issues: dict, score: dict) -> dict:
    """
    Monitor Agent — classifies all detected issues by severity
    and decides which ones need root cause investigation.
    """

    findings = []

    # Score-level alert
    if score["total"] < 40:
        level = "critical"
    elif score["total"] < 60:
        level = "high"
    elif score["total"] < 75:
        level = "medium"
    else:
        level = "low"

    # Missing values
    mv = issues["missing_values"]
    if mv["count"] > 0:
        for col, cnt in mv["columns"].items():
            findings.append({
                "issue_type": "missing_values",
                "column":     col,
                "count":      cnt,
                "severity":   _severity(cnt, issues["missing_values"]["count"]),
                "message":    f"{cnt} missing values in column '{col}'",
            })

    # Duplicates
    if issues["duplicates"]["count"] > 0:
        findings.append({
            "issue_type": "duplicates",
            "column":     "entire_row",
            "count":      issues["duplicates"]["count"],
            "severity":   "high",
            "message":    f"{issues['duplicates']['count']} duplicate rows detected",
        })

    # Outliers
    for col, info in issues["outliers"].items():
        findings.append({
            "issue_type": "outlier",
            "column":     col,
            "count":      info["count"],
            "severity":   "high",
            "message":    f"{info['count']} outlier(s) in '{col}' outside [{info['bounds']['lower']}, {info['bounds']['upper']}]",
        })

    # Invalid values
    for key, info in issues["invalid_values"].items():
        findings.append({
            "issue_type": "invalid_value",
            "column":     key,
            "count":      info["count"],
            "severity":   "medium",
            "message":    f"{info['count']} invalid value(s) — {key}",
        })

    # Type issues
    for col, info in issues["type_issues"].items():
        findings.append({
            "issue_type": "type_issue",
            "column":     col,
            "count":      len(info["bad_rows"]),
            "severity":   "high",
            "message":    info["message"],
        })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda x: severity_order.get(x["severity"], 4))

    return {
        "agent":          "MonitorAgent",
        "overall_level":  level,
        "total_findings": len(findings),
        "findings":       findings,
    }


def _severity(col_count: int, total_missing: int) -> str:
    ratio = col_count / max(total_missing, 1)
    if ratio > 0.4:
        return "critical"
    if ratio > 0.2:
        return "high"
    return "medium"