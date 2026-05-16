import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from config.database import SessionLocal
from models.models import Tool, Trend

st.set_page_config(
    page_title = "AI Trends Engine — Admin",
    page_icon  = None,
    layout     = "wide",
)

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4f8ef7;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b92a5;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .trend-card {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 10px;
    }
    .status-rising   { color: #f7c948; }
    .status-exploding{ color: #f74f4f; }
    .status-strong   { color: #4ff7a0; }
    .status-weak     { color: #8b92a5; }
    .score-bar {
        background: #2d3250;
        border-radius: 4px;
        height: 6px;
        margin-top: 8px;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #2d3250;
        border-radius: 8px;
        background: #1e2130;
    }
    .stButton button {
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

def get_db():
    return SessionLocal()

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("AI Trends Engine")
st.sidebar.caption("Admin Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Trends",
        "Tools",
        "Pending Approval",
        "Published",
        "Rejected",
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Updated: {datetime.now().strftime('%d %b %Y %H:%M')}")

# ── home page ─────────────────────────────────────────────────────────────────
if page == "Home":
    st.title("AI Marketing Trends")
    st.caption("Internal admin dashboard for managing AI marketing tools and trends")
    st.markdown("---")

    db = get_db()

    total_tools  = db.query(Tool).count()
    total_trends = db.query(Trend).count()
    pending      = db.query(Trend).filter(Trend.status == 'new').count()
    published    = db.query(Trend).filter(Trend.status == 'published').count()
    rising       = db.query(Trend).filter(Trend.status == 'rising').count()
    rejected     = db.query(Trend).filter(Trend.status == 'rejected').count()

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Tools", total_tools)
    with col2:
        st.metric("Total Trends", total_trends)
    with col3:
        st.metric("Pending Review", pending)
    with col4:
        st.metric("Published", published)
    with col5:
        st.metric("Rising", rising)
    with col6:
        st.metric("Rejected", rejected)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recently Found Tools")
        recent_tools = db.query(Tool).order_by(
            Tool.created_at.desc()
        ).limit(10).all()

        if recent_tools:
            for tool in recent_tools:
                with st.expander(f"{tool.name} — {tool.category}"):
                    st.write(f"**Description:** {tool.description}")
                    st.write(f"**Pricing:** {tool.pricing}")
                    if tool.website_url:
                        st.write(f"**Website:** {tool.website_url}")
                    st.caption(
                        f"Found: {tool.date_found.strftime('%d %b %Y') if tool.date_found else 'Unknown'}"
                    )
        else:
            st.info("No tools found yet. Run the scrapers first.")

    with col2:
        st.subheader("Top Scoring Trends")
        top_trends = db.query(Trend).order_by(
            Trend.growth_score.desc()
        ).limit(10).all()

        if top_trends:
            for trend in top_trends:
                score  = trend.growth_score or 0
                status = trend.status or 'new'
                with st.expander(f"{trend.keyword.title()} — Score: {score}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Category:** {trend.category}")
                        st.write(f"**Status:** {status.upper()}")
                    with col_b:
                        st.progress(int(score))
                    if trend.summary:
                        st.caption(trend.summary)
        else:
            st.info("No trends found yet.")

    db.close()

# ── trends page ───────────────────────────────────────────────────────────────
elif page == "Trends":
    st.title("All Trends")
    st.caption("Review, approve or reject collected trends")
    st.markdown("---")

    db     = get_db()
    trends = db.query(Trend).order_by(Trend.growth_score.desc()).all()

    if not trends:
        st.info("No trends found yet.")
    else:
        # Filter
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "new", "rising", "strong", "exploding", "published", "rejected"]
        )

        filtered = trends if status_filter == "All" else [
            t for t in trends if t.status == status_filter
        ]

        st.caption(f"Showing {len(filtered)} trends")
        st.markdown("---")

        for trend in filtered:
            score  = trend.growth_score or 0
            status = trend.status or 'new'

            with st.expander(
                f"{trend.keyword.title()} | Score: {score} | {status.upper()}"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"**Keyword:** {trend.keyword}")
                    st.write(f"**Category:** {trend.category}")
                    st.write(f"**Status:** {status.upper()}")
                    st.write(f"**Growth Score:** {score} / 100")
                    st.write(f"**Search Growth:** {trend.search_growth}")
                    st.markdown("**AI Generated Summary:**")
                    st.info(trend.summary)

                with col2:
                    st.progress(int(score))
                    st.markdown("**Actions:**")

                    if st.button(
                        "Approve", key=f"t_approve_{trend.id}"
                    ):
                        trend.status = 'rising'
                        db.commit()
                        st.success("Approved")
                        st.rerun()

                    if st.button(
                        "Reject", key=f"t_reject_{trend.id}"
                    ):
                        trend.status = 'rejected'
                        db.commit()
                        st.error("Rejected")
                        st.rerun()

                    if st.button(
                        "Edit", key=f"t_edit_{trend.id}"
                    ):
                        st.session_state[f"editing_{trend.id}"] = True

                    if st.session_state.get(f"editing_{trend.id}"):
                        st.markdown("---")
                        new_keyword  = st.text_input(
                            "Keyword", trend.keyword, key=f"kw_{trend.id}"
                        )
                        new_summary  = st.text_area(
                            "Summary", trend.summary, key=f"sm_{trend.id}"
                        )
                        new_category = st.text_input(
                            "Category", trend.category, key=f"cat_{trend.id}"
                        )
                        if st.button("Save Changes", key=f"save_{trend.id}"):
                            trend.keyword  = new_keyword
                            trend.summary  = new_summary
                            trend.category = new_category
                            db.commit()
                            st.success("Saved")
                            st.session_state[f"editing_{trend.id}"] = False
                            st.rerun()

    db.close()

# ── tools page ────────────────────────────────────────────────────────────────
elif page == "Tools":
    st.title("All Tools")
    st.caption("Browse all collected AI marketing tools")
    st.markdown("---")

    db    = get_db()
    tools = db.query(Tool).order_by(Tool.created_at.desc()).all()

    if not tools:
        st.info("No tools found yet.")
    else:
        categories = list(set([t.category for t in tools if t.category]))
        categories.insert(0, "All Categories")
        selected = st.selectbox("Filter by Category", categories)

        filtered = tools if selected == "All Categories" else [
            t for t in tools if t.category == selected
        ]

        st.caption(f"Showing {len(filtered)} tools")
        st.markdown("---")

        for tool in filtered:
            with st.expander(f"{tool.name} — {tool.category}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Name:** {tool.name}")
                    st.write(f"**Category:** {tool.category}")
                    st.write(f"**Description:** {tool.description}")
                    st.write(f"**Pricing:** {tool.pricing}")
                with col2:
                    if tool.website_url:
                        st.write(f"**Website:** {tool.website_url}")
                    if tool.source_url:
                        st.write(f"**Source:** {tool.source_url}")
                    st.write(f"**Tags:** {tool.tags}")
                    st.caption(
                        f"Found: {tool.date_found.strftime('%d %b %Y') if tool.date_found else 'Unknown'}"
                    )

    db.close()

# ── pending page ──────────────────────────────────────────────────────────────
elif page == "Pending Approval":
    st.title("Pending Approval")
    st.caption("Trends waiting for your review before publishing")
    st.markdown("---")

    db      = get_db()
    pending = db.query(Trend).filter(Trend.status == 'new').all()

    if not pending:
        st.success("No trends pending approval.")
    else:
        st.warning(f"{len(pending)} trends waiting for review")
        st.markdown("---")

        for trend in pending:
            score = trend.growth_score or 0
            with st.expander(f"{trend.keyword.title()} | Score: {score}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Category:** {trend.category}")
                    st.write(f"**Growth Score:** {score} / 100")
                    st.progress(int(score))
                    if trend.summary:
                        st.info(trend.summary)
                with col2:
                    st.markdown("**Actions:**")
                    if st.button("Approve", key=f"p_approve_{trend.id}"):
                        trend.status = 'rising'
                        db.commit()
                        st.success("Approved")
                        st.rerun()
                    if st.button("Reject", key=f"p_reject_{trend.id}"):
                        trend.status = 'rejected'
                        db.commit()
                        st.error("Rejected")
                        st.rerun()

    db.close()

# ── published page ────────────────────────────────────────────────────────────
elif page == "Published":
    st.title("Published Trends")
    st.caption("Trends that have been published to WordPress")
    st.markdown("---")

    db        = get_db()
    published = db.query(Trend).filter(Trend.status == 'published').all()

    if not published:
        st.info("No published trends yet.")
    else:
        st.caption(f"{len(published)} trends published")
        for trend in published:
            with st.expander(f"{trend.keyword.title()} — Score: {trend.growth_score}"):
                st.write(f"**Category:** {trend.category}")
                st.write(f"**Growth Score:** {trend.growth_score} / 100")
                if trend.summary:
                    st.info(trend.summary)

    db.close()

# ── rejected page ─────────────────────────────────────────────────────────────
elif page == "Rejected":
    st.title("Rejected Trends")
    st.caption("Trends that were rejected from publishing")
    st.markdown("---")

    db       = get_db()
    rejected = db.query(Trend).filter(Trend.status == 'rejected').all()

    if not rejected:
        st.info("No rejected trends.")
    else:
        st.caption(f"{len(rejected)} trends rejected")
        for trend in rejected:
            with st.expander(f"{trend.keyword.title()} — Score: {trend.growth_score}"):
                st.write(f"**Category:** {trend.category}")
                st.write(f"**Growth Score:** {trend.growth_score} / 100")
                if st.button("Restore to Pending", key=f"r_restore_{trend.id}"):
                    trend.status = 'new'
                    db.commit()
                    st.success("Restored")
                    st.rerun()

    db.close()