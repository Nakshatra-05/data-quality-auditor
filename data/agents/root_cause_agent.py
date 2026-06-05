import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run(findings: list, filename: str, df_info: dict) -> list:
    """
    Root Cause Agent — investigates each finding and
    assigns a probable root cause with confidence score.
    """

    results = []

    for finding in findings:
        cause = _investigate(finding, filename, df_info)
        results.append({
            **finding,
            "root_cause":  cause["root_cause"],
            "confidence":  cause["confidence"],
            "explanation": cause["explanation"],
        })

    return results


def _investigate(finding: dict, filename: str, df_info: dict) -> dict:
    """Use LLM to reason about the probable root cause of an issue."""

    prompt = f"""You are a senior data engineer investigating a data quality issue.

Dataset: {filename}
Dataset info: {df_info['rows']} rows, {df_info['cols']} columns, columns: {df_info['column_names']}

Issue detected:
- Type: {finding['issue_type']}
- Column: {finding['column']}
- Count: {finding['count']} affected records
- Severity: {finding['severity']}
- Message: {finding['message']}

Based on your experience with enterprise data pipelines, identify:
1. The single most probable root cause of this issue (1 sentence)
2. Your confidence level as a percentage (0-100)
3. A brief explanation of your reasoning (2-3 sentences)

Respond ONLY in this exact format:
ROOT_CAUSE: <one sentence root cause>
CONFIDENCE: <number between 0 and 100>
EXPLANATION: <2-3 sentence explanation>
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        return _parse_response(response.choices[0].message.content)
    except Exception:
        return {
            "root_cause":  "Unable to determine root cause",
            "confidence":  0,
            "explanation": "LLM analysis failed for this finding.",
        }


def _parse_response(text: str) -> dict:
    """Parse the structured LLM response into a dict."""
    lines = text.strip().split("\n")
    result = {
        "root_cause":  "Unknown",
        "confidence":  50,
        "explanation": "",
    }

    for line in lines:
        if line.startswith("ROOT_CAUSE:"):
            result["root_cause"] = line.replace("ROOT_CAUSE:", "").strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = int(line.replace("CONFIDENCE:", "").strip().replace("%", ""))
            except ValueError:
                result["confidence"] = 50
        elif line.startswith("EXPLANATION:"):
            result["explanation"] = line.replace("EXPLANATION:", "").strip()

    return result