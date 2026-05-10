import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
from pytrends.request import TrendReq
from config.database import SessionLocal
from models.models import Trend, TrendSnapshot

# ── google trends ─────────────────────────────────────────────────────────────

# def get_search_growth(keyword: str) -> float:
#     """
#     Get search growth score for a keyword from Google Trends
#     Returns a score from 0-100
#     """
#     try:
#         print(f"    📊 Checking Google Trends for: {keyword}")

#         pytrends = TrendReq(hl='en-US', tz=360)

#         # Get interest over time (last 3 months)
#         pytrends.build_payload(
#             [keyword],
#             timeframe='today 3-m',
#             geo='',
#         )

#         data = pytrends.interest_over_time()

#         if data.empty:
#             print(f"    ⚠️  No trends data for: {keyword}")
#             return 0.0

#         # Get recent vs older values
#         values      = data[keyword].tolist()
#         total       = len(values)

#         if total < 4:
#             return float(values[-1]) if values else 0.0

#         # Compare last quarter vs first quarter
#         first_half  = values[:total//2]
#         second_half = values[total//2:]

#         avg_first   = sum(first_half) / len(first_half)
#         avg_second  = sum(second_half) / len(second_half)

#         # Calculate growth percentage
#         if avg_first == 0:
#             growth = avg_second
#         else:
#             growth = ((avg_second - avg_first) / avg_first) * 100

#         # Normalize to 0-100
#         score = min(100, max(0, 50 + growth))

#         print(f"    ✅ Search growth score: {score:.1f}")
#         return round(score, 2)

#     except Exception as e:
#         print(f"    ❌ Google Trends error for {keyword}: {e}")
#         return 0.0

def get_search_growth(keyword: str) -> float:
    """
    Get search growth score for a keyword from Google Trends
    Returns a score from 0-100
    """
    try:
        print(f"    📊 Checking Google Trends for: {keyword}")

        pytrends = TrendReq(
            hl='en-US',
            tz=360,
            timeout=(10, 25),
            retries=2,
            backoff_factor=0.5,
        )

        # Get interest over time (last 3 months)
        pytrends.build_payload(
            [keyword],
            timeframe='today 3-m',
            geo='',
        )

        # Wait a bit before making request
        time.sleep(10)

        data = pytrends.interest_over_time()

        if data.empty:
            print(f"    ⚠️  No trends data for: {keyword}")
            return fallback_score(keyword)

        # Get recent vs older values
        values      = data[keyword].tolist()
        total       = len(values)

        if total < 4:
            return float(values[-1]) if values else fallback_score(keyword)

        # Compare last half vs first half
        first_half  = values[:total//2]
        second_half = values[total//2:]

        avg_first   = sum(first_half) / len(first_half)
        avg_second  = sum(second_half) / len(second_half)

        # Calculate growth percentage
        if avg_first == 0:
            growth = avg_second
        else:
            growth = ((avg_second - avg_first) / avg_first) * 100

        # Normalize to 0-100
        score = min(100, max(0, 50 + growth))

        print(f"    ✅ Search growth score: {score:.1f}")
        return round(score, 2)

    except Exception as e:
        print(f"    ⚠️  Google Trends unavailable, using fallback scoring")
        return fallback_score(keyword)


def fallback_score(keyword: str) -> float:
    """
    Fallback scoring when Google Trends is unavailable
    Based on keyword relevance and known AI marketing trends
    """

    # Known high-growth AI marketing keywords
    exploding = [
        'ai seo', 'ai video', 'ai ugc', 'ai content',
        'ai ads', 'ai creative', 'generative ai marketing'
    ]

    # Rising keywords
    rising = [
        'ai marketing', 'ai copywriting', 'ai email',
        'ai social media', 'ai analytics', 'ai automation',
        'ai outreach', 'ai landing page', 'ai lead generation'
    ]

    keyword_lower = keyword.lower()

    if any(k in keyword_lower for k in exploding):
        score = 75.0
        print(f"    ✅ Fallback score (exploding category): {score}")
    elif any(k in keyword_lower for k in rising):
        score = 55.0
        print(f"    ✅ Fallback score (rising category): {score}")
    else:
        score = 40.0
        print(f"    ✅ Fallback score (default): {score}")

    return score

# ── scoring formula ───────────────────────────────────────────────────────────

def calculate_trend_score(
    search_growth: float,
    social_growth: float,
    product_velocity: float,
    directory_presence: float = 50.0,
    manual_quality: float     = 50.0,
) -> float:
    """
    Calculate overall trend score from 0-100

    Formula:
    (search_growth × 0.40)
    + (social_growth × 0.25)
    + (product_velocity × 0.20)
    + (directory_presence × 0.10)
    + (manual_quality × 0.05)
    """

    score = (
        (search_growth    * 0.40) +
        (social_growth    * 0.25) +
        (product_velocity * 0.20) +
        (directory_presence * 0.10) +
        (manual_quality   * 0.05)
    )

    return round(min(100, max(0, score)), 2)


def get_trend_status(score: float) -> str:
    """Convert score to status label"""
    if score >= 81:
        return 'exploding'
    elif score >= 61:
        return 'strong'
    elif score >= 31:
        return 'rising'
    else:
        return 'weak'


# ── snapshot saver ────────────────────────────────────────────────────────────

def save_snapshot(db, trend_id: int, search_score: float, overall_score: float):
    """Save daily snapshot for a trend"""
    try:
        snapshot = TrendSnapshot(
            trend_id     = trend_id,
            date         = datetime.now(),
            search_score = search_score,
            overall_score= overall_score,
        )
        db.add(snapshot)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"    ❌ Error saving snapshot: {e}")
        return False


# ── main scorer ───────────────────────────────────────────────────────────────

def score_all_trends():
    """Score all trends in the database"""

    print("\n🚀 Starting Trend Scorer...")
    print("=" * 50)

    db     = SessionLocal()
    trends = db.query(Trend).all()

    if not trends:
        print("❌ No trends found in database!")
        db.close()
        return

    print(f"📋 Found {len(trends)} trends to score\n")

    for trend in trends:
        print(f"\n📌 Scoring: {trend.keyword}")
        print(f"   Category: {trend.category}")

        # Step 1 - Get Google Trends search growth
        search_growth = get_search_growth(trend.keyword)

        # Step 2 - Use social growth from Reddit (stored as 50 default for now)
        social_growth = trend.social_growth or 50.0

        # Step 3 - Product velocity (default 50 for now)
        product_velocity = trend.product_velocity or 50.0

        # Step 4 - Calculate final score
        final_score = calculate_trend_score(
            search_growth    = search_growth,
            social_growth    = social_growth,
            product_velocity = product_velocity,
        )

        # Step 5 - Get status label
        status = get_trend_status(final_score)

        # Step 6 - Update trend in database
        trend.search_growth = search_growth
        trend.growth_score  = final_score
        trend.status        = status
        trend.updated_at    = datetime.now()
        db.commit()

        # Step 7 - Save snapshot
        save_snapshot(db, trend.id, search_growth, final_score)

        print(f"   🎯 Final Score : {final_score}")
        print(f"   📈 Status      : {status.upper()}")

        # Wait between requests to avoid Google blocking us
        print(f"   ⏳ Waiting 30 seconds before next keyword...")
        time.sleep(30)

    db.close()

    print("\n" + "=" * 50)
    print("✅ All trends scored successfully!")
    print("=" * 50)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    score_all_trends()