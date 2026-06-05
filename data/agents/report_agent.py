import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run(
    monitor_result: dict,
    root_cause_findings: list,
    recommendations: list,
    score: dict,
    filename: str,
) -> str:
    """
    Report Agent — synthesises all agent outputs into
    a single executive summary report.
    """

    # Build findings summary
    critical = [f for f in root_cause_findings if f["severity"] == "critical"]
    high     = [f for f in root_cause_findings if f["severity"] == "high"]
    medium   = [f for f in root_cause_findings if f["severity"] == "medium"]

    findings_summary = []
    for f in root_cause_findings[:6]:  # top 6 findings
        findings_summary.append(
            f"- [{f['severity'].upper()}] {f['message']} | "
            f"Root cause: {f['root_cause']} ({f['confidence']}% confidence)"
        )

    recs_summary = []
    for i, r in enumerate(recommendations[:3], 1):
        recs_summary.append(
            f"{i}. [{r['priority'].upper()}] {r['fix']} | Code: {r['code_hint']}"
        )

    prompt = f"""You are a Chief Data Officer writing an executive data quality report.

Dataset: {filename}
Overall Quality Score: {score['total']}/100 — Grade: {score['grade']}
Alert Level: {monitor_result['overall_level'].upper()}
Total Issues Found: {monitor_result['total_findings']}
Critical Issues: {len(critical)} | High: {len(high)} | Medium: {len(medium)}

Top Findings with Root Causes:
{chr(10).join(findings_summary)}

Recommended Actions:
{chr(10).join(recs_summary)}

Write a professional executive summary report with these exact sections:

## Executive Summary
(2-3 sentences: overall data health, business risk level, urgent action needed)

## Key Findings
(3-4 bullet points of the most important issues in business language)

## Root Cause Analysis
(2-3 sentences explaining the probable systemic causes)

## Action Plan
(3 prioritised actions with timeline: immediate/this week/this month)

## Risk if Unaddressed
(2 sentences on business consequences if issues are not fixed)

Keep it concise, professional, and free of technical jargon.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Report generation failed: {e}"