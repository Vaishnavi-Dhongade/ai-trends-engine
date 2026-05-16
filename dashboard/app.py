import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from config.database import SessionLocal
from models.models import Tool, Trend

st.set_page_config(
    page_title = "AI Trends Engine",
    page_icon  = "🚀",
    layout     = "wide",
)

def get_db():
    return SessionLocal()

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🚀 AI Trends Engine")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📈 Trends",
        "🛠️ Tools",
        "⏳ Pending Approval",
        "✅ Published",
        "❌ Rejected",
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%d %b %Y %H:%M')}")

# ── home page ─────────────────────────────────────────────────────────────────
if page == "🏠 Home":
    st.title("🚀 AI Marketing Trends Dashboard")
    st.markdown("---")

    db = get_db()

    col1, col2, col3, col4 = st.columns(4)
    total_tools  = db.query(Tool).count()
    total_trends = db.query(Trend).count()
    pending      = db.query(Trend).filter(Trend.status == 'new').count()
    published    = db.query(Trend).filter(Trend.status == 'published').count()

    with col1:
        st.metric("🛠️ Total Tools", total_tools)
    with col2:
        st.metric("📈 Total Trends", total_trends)
    with col3:
        st.metric("⏳ Pending Review", pending)
    with col4:
        st.metric("✅ Published", published)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🆕 Recently Found Tools")
        recent_tools = db.query(Tool).order_by(Tool.created_at.desc()).limit(10).all()
        if recent_tools:
            for tool in recent_tools:
                with st.expander(f"🛠️ {tool.name}"):
                    st.write(f"**Category:** {tool.category}")
                    st.write(f"**Description:** {tool.description}")
                    if tool.website_url:
                        st.write(f"**Website:** {tool.website_url}")
                    st.write(f"**Found:** {tool.date_found.strftime('%d %b %Y') if tool.date_found else 'Unknown'}")
        else:
            st.info("No tools found yet. Run the scrapers first!")

    with col2:
        st.subheader("🔥 Top Scoring Trends")
        top_trends = db.query(Trend).order_by(Trend.growth_score.desc()).limit(10).all()
        if top_trends:
            for trend in top_trends:
                score  = trend.growth_score or 0
                status = trend.status or 'new'
                color  = "🔴" if score >= 81 else "🟠" if score >= 61 else "🟡" if score >= 31 else "🟢"
                with st.expander(f"{color} {trend.keyword} — Score: {score}"):
                    st.write(f"**Category:** {trend.category}")
                    st.write(f"**Status:** {status.upper()}")
                    st.info(trend.summary)
        else:
            st.info("No trends found yet. Run the scrapers first!")

    db.close()

# ── trends page ───────────────────────────────────────────────────────────────
elif page == "📈 Trends":
    st.title("📈 All Trends")
    st.markdown("---")

    db     = get_db()
    trends = db.query(Trend).order_by(Trend.growth_score.desc()).all()

    if not trends:
        st.info("No trends found yet!")
    else:
        for trend in trends:
            score  = trend.growth_score or 0
            status = trend.status or 'new'

            with st.expander(f"📈 {trend.keyword} | Score: {score} | {status.upper()}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Keyword:** {trend.keyword}")
                    st.write(f"**Category:** {trend.category}")
                    st.write(f"**Status:** {status.upper()}")
                    st.write(f"**Growth Score:** {score}")
                    st.write(f"**Search Growth:** {trend.search_growth}")
                    st.markdown("**📝 AI Generated Summary:**")
                    st.info(trend.summary)

                with col2:
                    st.progress(int(score))
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        if st.button("✅ Approve", key=f"t_approve_{trend.id}"):
                            trend.status = 'rising'
                            db.commit()
                            st.success("Approved!")
                            st.rerun()

                    with col_b:
                        if st.button("❌ Reject", key=f"t_reject_{trend.id}"):
                            trend.status = 'rejected'
                            db.commit()
                            st.error("Rejected!")
                            st.rerun()

                    with col_c:
                        if st.button("📝 Edit", key=f"t_edit_{trend.id}"):
                            st.session_state[f"editing_{trend.id}"] = True

                    if st.session_state.get(f"editing_{trend.id}"):
                        st.markdown("**Edit Trend:**")
                        new_keyword  = st.text_input("Keyword",  trend.keyword,  key=f"kw_{trend.id}")
                        new_summary  = st.text_area("Summary",   trend.summary,  key=f"sm_{trend.id}")
                        new_category = st.text_input("Category", trend.category, key=f"cat_{trend.id}")

                        if st.button("💾 Save", key=f"save_{trend.id}"):
                            trend.keyword  = new_keyword
                            trend.summary  = new_summary
                            trend.category = new_category
                            db.commit()
                            st.success("Saved!")
                            st.session_state[f"editing_{trend.id}"] = False
                            st.rerun()

    db.close()

# ── tools page ────────────────────────────────────────────────────────────────
elif page == "🛠️ Tools":
    st.title("🛠️ All Tools")
    st.markdown("---")

    db    = get_db()
    tools = db.query(Tool).order_by(Tool.created_at.desc()).all()

    if not tools:
        st.info("No tools found yet!")
    else:
        categories = list(set([t.category for t in tools if t.category]))
        categories.insert(0, "All Categories")
        selected = st.selectbox("Filter by Category", categories)
        filtered = tools if selected == "All Categories" else [
            t for t in tools if t.category == selected
        ]
        st.write(f"Showing **{len(filtered)}** tools")
        st.markdown("---")

        for tool in filtered:
            with st.expander(f"🛠️ {tool.name} — {tool.category}"):
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
                    st.write(f"**Found:** {tool.date_found.strftime('%d %b %Y') if tool.date_found else 'Unknown'}")

    db.close()

# ── pending page ──────────────────────────────────────────────────────────────
elif page == "⏳ Pending Approval":
    st.title("⏳ Trends Pending Approval")
    st.markdown("---")

    db      = get_db()
    pending = db.query(Trend).filter(Trend.status == 'new').all()

    if not pending:
        st.success("No trends pending approval!")
    else:
        st.warning(f"**{len(pending)} trends** waiting for your review")
        st.markdown("---")

        for trend in pending:
            score = trend.growth_score or 0
            with st.expander(f"⏳ {trend.keyword} | Score: {score}"):
                st.write(f"**Category:** {trend.category}")
                st.info(trend.summary)
                st.write(f"**Growth Score:** {score}")
                st.progress(int(score))

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", key=f"p_approve_{trend.id}"):
                        trend.status = 'rising'
                        db.commit()
                        st.success("Approved!")
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"p_reject_{trend.id}"):
                        trend.status = 'rejected'
                        db.commit()
                        st.error("Rejected!")
                        st.rerun()

    db.close()

# ── published page ────────────────────────────────────────────────────────────
elif page == "✅ Published":
    st.title("✅ Published Trends")
    st.markdown("---")

    db        = get_db()
    published = db.query(Trend).filter(Trend.status == 'published').all()

    if not published:
        st.info("No published trends yet!")
    else:
        for trend in published:
            with st.expander(f"✅ {trend.keyword}"):
                st.write(f"**Category:** {trend.category}")
                st.write(f"**Score:** {trend.growth_score}")
                st.info(trend.summary)

    db.close()

# ── rejected page ─────────────────────────────────────────────────────────────
elif page == "❌ Rejected":
    st.title("❌ Rejected Trends")
    st.markdown("---")

    db       = get_db()
    rejected = db.query(Trend).filter(Trend.status == 'rejected').all()

    if not rejected:
        st.info("No rejected trends yet!")
    else:
        for trend in rejected:
            with st.expander(f"❌ {trend.keyword}"):
                st.write(f"**Category:** {trend.category}")
                st.write(f"**Score:** {trend.growth_score}")
                if st.button("♻️ Restore", key=f"r_restore_{trend.id}"):
                    trend.status = 'new'
                    db.commit()
                    st.success("Restored!")
                    st.rerun()

    db.close()