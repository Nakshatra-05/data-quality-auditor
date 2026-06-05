import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data.validator import run_all_checks
from data.scorer import calculate_score
from data.llm_analyst import generate_analysis
from data.schema_drift import detect_schema_drift, summarise_drift
from data.monitoring import save_run, load_history, get_trend
from data.agents import monitor_agent, root_cause_agent, recommendation_agent, report_agent

# ── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="Data Quality Auditor",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 AI Data Quality Auditor")
st.caption("Upload any CSV to get an instant quality score, issue breakdown, and AI-powered business analysis.")

# ── Main navigation tabs ──────────────────────────────────
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
    "📊 Audit",
    "🔄 Schema Drift",
    "📈 History",
    "🤖 Agent",
])
# ════════════════════════════════════════════════════════════
# TAB 1 — AUDIT
# ════════════════════════════════════════════════════════════
with main_tab1:

    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if not uploaded_file:
        st.info("Upload a CSV file above to get started.")
        st.stop()

    df = pd.read_csv(uploaded_file)
    filename = uploaded_file.name

    st.success(f"Loaded **{filename}** — {len(df)} rows × {len(df.columns)} columns")

    with st.expander("Preview data (first 20 rows)"):
        st.dataframe(df.head(20), use_container_width=True)

    # Run checks
    with st.spinner("Running data quality checks..."):
        issues = run_all_checks(df)
        score  = calculate_score(issues, len(df))

    # Auto save to history
    save_run(filename, score, issues)

    # ── Data Health Card ──────────────────────────────────────
    st.divider()

    # Color based on score
    if score["total"] >= 90:
        circle_color = "#4CAF50"
        bg_color     = "#1a2e1a"
        label        = "Excellent"
    elif score["total"] >= 75:
        circle_color = "#2196F3"
        bg_color     = "#1a1f2e"
        label        = "Good"
    elif score["total"] >= 60:
        circle_color = "#FF9800"
        bg_color     = "#2e1a0e"
        label        = "Fair"
    elif score["total"] >= 40:
        circle_color = "#f44336"
        bg_color     = "#2e1a1a"
        label        = "Poor"
    else:
        circle_color = "#b71c1c"
        bg_color     = "#2e0a0a"
        label        = "Critical"

    st.markdown(f"""
    <div style="background:{bg_color};border:1px solid {circle_color};
                border-radius:16px;padding:28px 32px;margin-bottom:16px;
                display:flex;align-items:center;gap:40px;">
        <div style="text-align:center;min-width:120px;">
            <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none"
                        stroke="#333" stroke-width="10"/>
                <circle cx="60" cy="60" r="52" fill="none"
                        stroke="{circle_color}" stroke-width="10"
                        stroke-dasharray="{int(score['total'] * 3.27)} 327"
                        stroke-linecap="round"
                        transform="rotate(-90 60 60)"/>
                <text x="60" y="55" text-anchor="middle"
                      fill="{circle_color}" font-size="26"
                      font-weight="bold" font-family="sans-serif">
                    {score['total']}
                </text>
                <text x="60" y="74" text-anchor="middle"
                      fill="#aaa" font-size="12"
                      font-family="sans-serif">/ 100</text>
            </svg>
            <div style="color:{circle_color};font-weight:600;
                        font-size:16px;margin-top:4px;">{label}</div>
        </div>
        <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:14px;">
                <div style="color:#aaa;font-size:12px;margin-bottom:4px;">Missing Cells</div>
                <div style="color:#fff;font-size:22px;font-weight:600;">
                    {issues['missing_values']['count']}
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:14px;">
                <div style="color:#aaa;font-size:12px;margin-bottom:4px;">Duplicates</div>
                <div style="color:#fff;font-size:22px;font-weight:600;">
                    {issues['duplicates']['count']}
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:14px;">
                <div style="color:#aaa;font-size:12px;margin-bottom:4px;">Outlier Columns</div>
                <div style="color:#fff;font-size:22px;font-weight:600;">
                    {len(issues['outliers'])}
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:14px;">
                <div style="color:#aaa;font-size:12px;margin-bottom:4px;">Invalid Records</div>
                <div style="color:#fff;font-size:22px;font-weight:600;">
                    {sum(v['count'] for v in issues['invalid_values'].values())}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Score breakdown chart ─────────────────────────────
    st.divider()
    st.subheader("Score Breakdown by Dimension")

    breakdown = score["breakdown"]
    fig_bar = px.bar(
        x=list(breakdown.keys()),
        y=list(breakdown.values()),
        labels={"x": "Dimension", "y": "Score (0-100)"},
        color=list(breakdown.values()),
        color_continuous_scale=["red", "orange", "green"],
        range_color=[0, 100],
        text_auto=True,
    )
    fig_bar.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        height=350,
        yaxis_range=[0, 110],
    )
    fig_bar.update_traces(textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Issue details tabs ────────────────────────────────
    st.divider()
    st.subheader("Issue Details")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔴 Missing Values",
        "🟠 Duplicates",
        "🟡 Outliers",
        "🔵 Invalid Values",
        "⚪ Type Issues",
    ])

    with tab1:
        mv = issues["missing_values"]
        if mv["count"] == 0:
            st.success("No missing values found.")
        else:
            st.warning(f"{mv['count']} missing cells across {len(mv['columns'])} column(s)")
            fig = px.bar(
                x=list(mv["columns"].keys()),
                y=list(mv["columns"].values()),
                labels={"x": "Column", "y": "Missing Count"},
                color=list(mv["columns"].values()),
                color_continuous_scale=["orange", "red"],
                text_auto=True,
            )
            fig.update_layout(coloraxis_showscale=False, height=300)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        d = issues["duplicates"]
        if d["count"] == 0:
            st.success("No duplicate rows found.")
        else:
            st.warning(f"{d['count']} duplicate row(s) detected")
            st.dataframe(df.iloc[d["rows"]], use_container_width=True)

    with tab3:
        o = issues["outliers"]
        if not o:
            st.success("No outliers detected.")
        else:
            for col, info in o.items():
                with st.expander(f"📊 {col} — {info['count']} outlier(s)"):
                    st.write(f"**Valid range:** {info['bounds']['lower']} to {info['bounds']['upper']}")
                    st.write(f"**Outlier values:** {info['values']}")
                    fig = px.box(df[col].dropna(), title=f"Boxplot — {col}")
                    st.plotly_chart(fig, use_container_width=True)

    with tab4:
        iv = issues["invalid_values"]
        if not iv:
            st.success("No invalid values found.")
        else:
            for check, info in iv.items():
                with st.expander(f"⚠️ {check} — {info['count']} issue(s)"):
                    st.write(f"**Affected rows:** {info['rows']}")
                    st.write(f"**Values:** {info['values']}")

    with tab5:
        ti = issues["type_issues"]
        if not ti:
            st.success("No type issues found.")
        else:
            for col, info in ti.items():
                with st.expander(f"⚠️ {col}"):
                    st.write(f"**Issue:** {info['message']}")
                    st.write(f"**Bad rows:** {info['bad_rows']}")
                    st.write(f"**Bad values:** {info['bad_values']}")

    # ── AI Analysis ───────────────────────────────────────
    st.divider()
    st.subheader("🤖 AI Business Impact Analysis")
    st.caption("Powered by Groq (LLaMA 3.3) — explains findings in business language and recommends fixes.")

    if st.button("Generate AI Analysis", type="primary"):
        with st.spinner("Analysing your data quality findings..."):
            try:
                analysis = generate_analysis(issues, score, filename)
                st.markdown(analysis)
            except Exception as e:
                st.error(f"LLM API error: {e}")


# ════════════════════════════════════════════════════════════
# TAB 2 — SCHEMA DRIFT
# ════════════════════════════════════════════════════════════
with main_tab2:

    st.subheader("🔄 Schema Drift Detection")
    st.caption("Upload two versions of the same dataset to detect structural changes.")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Baseline CSV** (older version)")
        file_old = st.file_uploader("Upload baseline CSV", type=["csv"], key="old")

    with col_b:
        st.markdown("**Current CSV** (newer version)")
        file_new = st.file_uploader("Upload current CSV", type=["csv"], key="new")

    if file_old and file_new:
        df_old = pd.read_csv(file_old)
        df_new = pd.read_csv(file_new)

        with st.spinner("Comparing schemas..."):
            drift = detect_schema_drift(df_old, df_new)

        summary = summarise_drift(drift)

        if drift["drift_detected"]:
            st.error(f"⚠️ Schema drift detected — {summary}")
        else:
            st.success("✅ " + summary)

        st.divider()

        # Row count comparison
        st.subheader("Row Count Comparison")
        rc = drift["row_count"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline rows", rc["old"])
        c2.metric("Current rows",  rc["new"])
        c3.metric("Difference",    rc["diff"], delta=rc["diff"])

        # Added / removed columns
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Added Columns")
            if drift["added_columns"]:
                for col in drift["added_columns"]:
                    st.success(f"➕ {col}")
            else:
                st.info("None")

        with col2:
            st.subheader("Removed Columns")
            if drift["removed_columns"]:
                for col in drift["removed_columns"]:
                    st.error(f"➖ {col}")
            else:
                st.info("None")

        # Type changes
        st.subheader("Data Type Changes")
        if drift["type_changes"]:
            for col, info in drift["type_changes"].items():
                st.warning(f"**{col}**: `{info['old_type']}` → `{info['new_type']}`")
        else:
            st.success("No data type changes detected.")

        # Null rate changes
        st.subheader("Null Rate Changes (≥ 5%)")
        if drift["null_rate_changes"]:
            for col, info in drift["null_rate_changes"].items():
                direction = "📈" if info["change"] > 0 else "📉"
                st.warning(
                    f"{direction} **{col}**: {info['old_null_rate']}% → "
                    f"{info['new_null_rate']}% (change: {info['change']:+.2f}%)"
                )
        else:
            st.success("No significant null rate changes detected.")

    else:
        st.info("Upload both CSV files above to start drift detection.")


# ════════════════════════════════════════════════════════════
# TAB 3 — HISTORY
# ════════════════════════════════════════════════════════════
with main_tab3:

    st.subheader("📈 Quality Score History")
    st.caption("Every scan is automatically saved. Track quality trends over time.")

    records = load_history()

    if not records:
        st.info("No history yet. Run an audit in the Audit tab to start tracking.")
    else:
        trend = get_trend(records)

        # Trend line chart
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend["dates"],
            y=trend["scores"],
            mode="lines+markers+text",
            text=trend["scores"],
            textposition="top center",
            line=dict(color="#4CAF50", width=2),
            marker=dict(size=8),
            name="Quality Score",
        ))
        fig_trend.add_hline(y=75, line_dash="dash", line_color="orange",
                            annotation_text="Good threshold (75)")
        fig_trend.add_hline(y=90, line_dash="dash", line_color="green",
                            annotation_text="Excellent threshold (90)")
        fig_trend.update_layout(
            title="Quality Score Over Time",
            xaxis_title="Scan Date",
            yaxis_title="Score",
            yaxis_range=[0, 110],
            height=400,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.divider()

        # History table
        st.subheader("All Scan Records")
        table_data = []
        for r in reversed(records):
            table_data.append({
                "File":          r["filename"],
                "Scanned At":    r["scanned_at"],
                "Score":         r["score"]["total"],
                "Grade":         r["score"]["grade"],
                "Missing Cells": r["summary"]["missing_cells"],
                "Duplicates":    r["summary"]["duplicates"],
            })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

# ════════════════════════════════════════════════════════════
# TAB 4 — AGENTIC ROOT CAUSE ANALYSIS
# ════════════════════════════════════════════════════════════
with main_tab4:

    # Header banner
    st.markdown("## 🤖 Agentic Root Cause Analysis")
    st.caption("Multi-agent AI pipeline — monitors, investigates, recommends, and reports")

    # Agent pills
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.info("📡 Monitor Agent\nClassifies issues by severity")
    col_b.warning("🔬 Root Cause Agent\nInvestigates why issues exist")
    col_c.info("💡 Recommendation Agent\nGenerates specific code fixes")
    col_d.success("📝 Report Agent\nWrites executive summary")

    st.divider()

    agent_file = st.file_uploader("Upload CSV for agent analysis", type=["csv"], key="agent")

    if not agent_file:
        st.info("Upload a CSV file above to start the agent pipeline.")

    else:
        df_agent   = pd.read_csv(agent_file)
        agent_name = agent_file.name

        st.success(f"Loaded **{agent_name}** — {len(df_agent)} rows × {len(df_agent.columns)} columns")

        if st.button("🚀 Run Agent Pipeline", type="primary"):

            # ── Pipeline progress ─────────────────────────
            steps = [
                ("🔍", "Step 1 — Validating dataset"),
                ("📡", "Step 2 — Monitor Agent classifying issues"),
                ("🔬", "Step 3 — Root Cause Agent investigating"),
                ("💡", "Step 4 — Recommendation Agent generating fixes"),
                ("📝", "Step 5 — Report Agent writing executive summary"),
            ]

            progress_bar = st.progress(0, text="Starting pipeline...")
            status_box   = st.empty()

            def update_status(step_idx: int, message: str):
                progress_bar.progress(
                    int((step_idx / len(steps)) * 100),
                    text=message
                )
                status_box.info(f"{steps[step_idx][0]} {steps[step_idx][1]}...")

            # ── Stage 1: Validate ─────────────────────────
            update_status(0, "Validating dataset...")
            issues_agent = run_all_checks(df_agent)
            score_agent  = calculate_score(issues_agent, len(df_agent))

            # ── Stage 2: Monitor Agent ─────────────────────
            update_status(1, "Monitor Agent classifying issues...")
            monitor_result = monitor_agent.run(issues_agent, score_agent)

            # ── Stage 3: Root Cause Agent ──────────────────
            update_status(2, "Root Cause Agent investigating...")
            df_info = {
                "rows":         len(df_agent),
                "cols":         len(df_agent.columns),
                "column_names": list(df_agent.columns),
            }
            root_causes = root_cause_agent.run(
                monitor_result["findings"][:6],
                agent_name,
                df_info,
            )

            # ── Stage 4: Recommendation Agent ─────────────
            update_status(3, "Recommendation Agent generating fixes...")
            recommendations = recommendation_agent.run(root_causes, agent_name)

            # ── Stage 5: Report Agent ──────────────────────
            update_status(4, "Report Agent writing executive summary...")
            report = report_agent.run(
                monitor_result,
                root_causes,
                recommendations,
                score_agent,
                agent_name,
            )

            progress_bar.progress(100, text="Pipeline complete!")
            status_box.success("✅ Agent pipeline complete!")

            st.divider()

            # ── Score banner ──────────────────────────────
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Quality Score",  f"{score_agent['total']} / 100")
            col2.metric("Grade",          score_agent["grade"])
            col3.metric("Total Findings", monitor_result["total_findings"])
            col4.metric("Alert Level",    monitor_result["overall_level"].upper())

            st.divider()

            # ── Monitor findings ──────────────────────────
            st.subheader("📡 Monitor Agent — Issue Classification")
            severity_icons = {
                "critical": "🔴",
                "high":     "🟠",
                "medium":   "🟡",
                "low":      "🟢",
            }
            for f in monitor_result["findings"]:
                icon = severity_icons.get(f["severity"], "⚪")
                st.write(f"{icon} **{f['severity'].upper()}** — {f['message']}")

            st.divider()

            # ── Root cause findings ───────────────────────
            st.subheader("🔬 Root Cause Agent — Investigation Results")
            for i, f in enumerate(root_causes, 1):
                icon = severity_icons.get(f["severity"], "⚪")
                with st.expander(f"{i}. {icon} [{f['severity'].upper()}] {f['column']} — {f['issue_type']}"):
                    st.markdown("**Issue:**")
                    st.write(f["message"])
                    st.markdown("**Root Cause:**")
                    st.warning(f["root_cause"])
                    st.markdown("**Explanation:**")
                    st.write(f["explanation"])
                    st.progress(
                        f["confidence"] / 100,
                        text=f"Confidence: {f['confidence']}%"
                    )

            st.divider()

            # ── Recommendations ───────────────────────────
            st.subheader("💡 Recommendation Agent — Action Items")
            priority_icons = {
                "immediate":  "🔴",
                "short-term": "🟡",
                "long-term":  "🟢",
            }
            for i, r in enumerate(recommendations, 1):
                icon = priority_icons.get(r["priority"], "⚪")
                with st.expander(f"{icon} {i}. [{r['priority'].upper()}] {r['column']} — {r['issue_type']}"):
                    st.markdown("**Fix:**")
                    st.write(r["fix"])
                    st.markdown("**Code hint:**")
                    st.code(r["code_hint"], language="python")
                    st.caption(f"Root cause: {r['root_cause']} ({r['confidence']}% confidence)")

            st.divider()

            # ── Executive report ──────────────────────────
            st.subheader("📝 Report Agent — Executive Summary")
            st.markdown(report)