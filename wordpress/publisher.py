import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from dotenv import load_dotenv
from config.database import SessionLocal
from models.models import Trend, Tool

load_dotenv()

# ── WordPress credentials ─────────────────────────────────────────────────────

WP_URL      = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# ── helpers ───────────────────────────────────────────────────────────────────

def get_headers():
    """Get authentication headers for WordPress REST API"""
    import base64
    credentials = f"{WP_USERNAME}:{WP_PASSWORD}"
    token       = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type" : "application/json",
    }


def test_connection() -> bool:
    """Test if WordPress REST API is accessible"""
    try:
        print("🔌 Testing WordPress connection...")
        response = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts",
            headers = get_headers(),
            timeout = 10,
        )
        if response.status_code == 200:
            print("✅ WordPress connection successful!")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


# ── publish trend ─────────────────────────────────────────────────────────────

def publish_trend(trend) -> bool:
    """Publish a single trend to WordPress as a post"""
    try:
        print(f"\n📤 Publishing trend: {trend.keyword}")

        # Build post content
        content = f"""
<h2>About This Trend</h2>
<p>{trend.summary}</p>

<h2>Trend Details</h2>
<ul>
    <li><strong>Category:</strong> {trend.category}</li>
    <li><strong>Growth Score:</strong> {trend.growth_score}/100</li>
    <li><strong>Status:</strong> {trend.status}</li>
    <li><strong>Search Growth:</strong> {trend.search_growth}</li>
</ul>

<h2>Growth Score Breakdown</h2>
<p>This trend scored <strong>{trend.growth_score}/100</strong> based on:</p>
<ul>
    <li>Search volume growth</li>
    <li>Social media mentions</li>
    <li>Product Hunt velocity</li>
    <li>Directory presence</li>
</ul>
"""

        # WordPress post data
        post_data = {
            "title"   : trend.keyword.title(),
            "content" : content,
            "status"  : "publish",
            "slug"    : trend.slug,
            "excerpt" : trend.summary[:150] if trend.summary else "",
            "categories": [],
            "tags"    : [],
        }

        # Send to WordPress
        response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            headers = get_headers(),
            json    = post_data,
            timeout = 30,
        )

        if response.status_code in [200, 201]:
            wp_post = response.json()
            print(f"✅ Published successfully!")
            print(f"   WordPress Post ID : {wp_post.get('id')}")
            print(f"   WordPress URL     : {wp_post.get('link')}")

            # Update trend status in database
            db = SessionLocal()
            db_trend = db.query(Trend).filter(Trend.id == trend.id).first()
            if db_trend:
                db_trend.status = 'published'
                db.commit()
            db.close()

            return True

        else:
            print(f"❌ Publishing failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"❌ Error publishing trend: {e}")
        return False


# ── publish tool ──────────────────────────────────────────────────────────────

def publish_tool(tool) -> bool:
    """Publish a single tool to WordPress as a post"""
    try:
        print(f"\n📤 Publishing tool: {tool.name}")

        # Build post content
        content = f"""
<h2>About {tool.name}</h2>
<p>{tool.description}</p>

<h2>Tool Details</h2>
<ul>
    <li><strong>Category:</strong> {tool.category}</li>
    <li><strong>Pricing:</strong> {tool.pricing}</li>
    <li><strong>Tags:</strong> {tool.tags}</li>
</ul>

<h2>Links</h2>
<ul>
    <li><a href="{tool.website_url}" target="_blank">Visit Website</a></li>
</ul>
"""

        post_data = {
            "title"  : tool.name,
            "content": content,
            "status" : "publish",
            "slug"   : tool.slug,
            "excerpt": tool.description[:150] if tool.description else "",
        }

        response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            headers = get_headers(),
            json    = post_data,
            timeout = 30,
        )

        if response.status_code in [200, 201]:
            wp_post = response.json()
            print(f"✅ Tool published successfully!")
            print(f"   WordPress Post ID: {wp_post.get('id')}")
            return True
        else:
            print(f"❌ Publishing failed: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False

    except Exception as e:
        print(f"❌ Error publishing tool: {e}")
        return False


# ── main function ─────────────────────────────────────────────────────────────

def publish_all_approved():
    """Publish all approved trends to WordPress"""

    print("\n🚀 Starting WordPress Publisher...")
    print("=" * 50)

    # Test connection first
    if not test_connection():
        print("❌ Cannot connect to WordPress. Check your .env file.")
        return

    db      = SessionLocal()
    trends  = db.query(Trend).filter(
        Trend.status.in_(['rising', 'strong', 'exploding'])
    ).all()

    print(f"\n📋 Found {len(trends)} approved trends to publish")

    published = 0
    failed    = 0

    for trend in trends:
        if publish_trend(trend):
            published += 1
        else:
            failed += 1

    db.close()

    print("\n" + "=" * 50)
    print(f"✅ Publishing complete!")
    print(f"   Published : {published}")
    print(f"   Failed    : {failed}")
    print("=" * 50)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    publish_all_approved()