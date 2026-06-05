SCORE_WEIGHTS = {
    "missing_values": 0.25,
    "duplicates":     0.20,
    "outliers":       0.25,
    "invalid_values": 0.20,
    "type_issues":    0.10,
}

GRADE_THRESHOLDS = {
    "Excellent": 90,
    "Good":      75,
    "Fair":      60,
    "Poor":      40,
}

PENALTY_MULTIPLIERS = {
    "missing_values": 200,
    "duplicates":     300,
    "outliers":       250,
    "invalid_values": 300,
    "type_issues":    20,
}