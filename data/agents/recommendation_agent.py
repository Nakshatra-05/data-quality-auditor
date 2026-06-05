import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run(root_cause_findings: list, filename: str) -> list:
    """
    Recommendation Agent — takes root cause findings and
    generates specific, actionable fix recommendations.
    """

    # Only recommend for high/critical severity findings
    priority_findings = [
        f for f in root_cause_findings
        if f["severity"] in ("critical", "high")
    ]

    # If nothing critical, take top 3 medium ones
    if not priority_findings:
        priority_findings = root_cause_findings[:3]

    recommendations = []
    for finding in priority_findings:
        rec = _recommend(finding, filename)
        recommendations.append({
            "issue_type":    finding["issue_type"],
            "column":        finding["column"],
            "severity":      finding["severity"],
            "root_cause":    finding["root_cause"],
            "confidence":    finding["confidence"],
            "fix":           rec["fix"],
            "code_hint":     rec["code_hint"],
            "priority":      rec["priority"],
        })

    return recommendations


def _recommend(finding: dict, filename: str) -> dict:
    """Use LLM to generate a specific fix for this finding."""

    prompt = f"""You are a senior data engineer recommending fixes for data quality issues.

Dataset: {filename}
Issue:
- Type: {finding['issue_type']}
- Column: {finding['column']}
- Root Cause: {finding['root_cause']}
- Confidence: {finding['confidence']}%
- Message: {finding['message']}

Provide:
1. A specific, actionable fix recommendation (1-2 sentences)
2. A short Python/Pandas code hint to fix this issue (1-3 lines max)
3. Priority level: immediate / short-term / long-term

Respond ONLY in this exact format:
FIX: <specific fix recommendation>
CODE: <short pandas code hint>
PRIORITY: <immediate or short-term or long-term>
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=250,
        )
        return _parse_response(response.choices[0].message.content)
    except Exception:
        return {
            "fix":       "Manual review recommended.",
            "code_hint": "# Review this column manually",
            "priority":  "short-term",
        }


def _parse_response(text: str) -> dict:
    """Parse structured LLM response into a dict."""
    lines = text.strip().split("\n")
    result = {
        "fix":       "Review this issue manually.",
        "code_hint": "# No code hint available",
        "priority":  "short-term",
    }

    for line in lines:
        if line.startswith("FIX:"):
            result["fix"] = line.replace("FIX:", "").strip()
        elif line.startswith("CODE:"):
            result["code_hint"] = line.replace("CODE:", "").strip()
        elif line.startswith("PRIORITY:"):
            result["priority"] = line.replace("PRIORITY:", "").strip().lower()

    return result