import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_analysis(issues: dict, score: dict, filename: str) -> str:

    missing_cols = list(issues["missing_values"]["columns"].keys())
    outlier_cols = list(issues["outliers"].keys())
    invalid_keys = list(issues["invalid_values"].keys())
    type_issue_cols = list(issues["type_issues"].keys())

    issue_lines = []

    if issues["missing_values"]["count"] > 0:
        issue_lines.append(
            f"- Missing values: {issues['missing_values']['count']} total cells affected "
            f"across columns: {', '.join(missing_cols)}"
        )

    if issues["duplicates"]["count"] > 0:
        issue_lines.append(
            f"- Duplicate records: {issues['duplicates']['count']} duplicate rows found"
        )

    if outlier_cols:
        for col, info in issues["outliers"].items():
            issue_lines.append(
                f"- Outlier in '{col}': {info['count']} value(s) outside "
                f"range [{info['bounds']['lower']}, {info['bounds']['upper']}]"
            )

    if invalid_keys:
        for key, info in issues["invalid_values"].items():
            issue_lines.append(
                f"- Invalid values ({key}): {info['count']} record(s) affected"
            )

    if type_issue_cols:
        for col, info in issues["type_issues"].items():
            issue_lines.append(f"- Type issue in '{col}': {info['message']}")

    issues_text = "\n".join(issue_lines) if issue_lines else "No major issues found."

    prompt = f"""You are a senior data quality analyst at an enterprise company.

A dataset named '{filename}' was scanned by our automated Data Quality Auditor.

Overall Quality Score: {score['total']}/100 — Grade: {score['grade']}

Score Breakdown:
- Missing Values Score: {score['breakdown']['missing_values']}/100
- Duplicates Score: {score['breakdown']['duplicates']}/100
- Outliers Score: {score['breakdown']['outliers']}/100
- Invalid Values Score: {score['breakdown']['invalid_values']}/100
- Type Issues Score: {score['breakdown']['type_issues']}/100

Detailed Findings:
{issues_text}

Your task:
1. Write a 4-5 sentence business impact summary in plain English explaining what these
   issues mean for the business — not technical jargon.
2. Explain which issues are most critical and why.
3. Provide exactly 3 specific, actionable recommendations to fix the data.

Format your response as:
## Business Impact Summary
(your paragraph here)

## Most Critical Issues
(your paragraph here)

## Recommendations
1. ...
2. ...
3. ...
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )

    return response.choices[0].message.content