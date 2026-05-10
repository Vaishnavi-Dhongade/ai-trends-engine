import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
import json
from datetime import datetime
from sqlalchemy.orm import Session
from config.database import SessionLocal
from models.models import Tool
import re

# ── helpers ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text.strip('-')


def is_duplicate(db: Session, name: str) -> bool:
    """Check if tool already exists in database"""
    existing = db.query(Tool).filter(Tool.name == name).first()
    return existing is not None


def save_tool(db: Session, tool_data: dict) -> bool:
    """Save a single tool to database"""
    try:
        # Check for duplicate first
        if is_duplicate(db, tool_data['name']):
            print(f"  ⚠️  Duplicate skipped: {tool_data['name']}")
            return False

        tool = Tool(
            name        = tool_data['name'],
            slug        = slugify(tool_data['name']),
            description = tool_data.get('description', ''),
            website_url = tool_data.get('website_url', ''),
            source_url  = tool_data.get('source_url', ''),
            category    = tool_data.get('category', 'AI Marketing Tool'),
            pricing     = tool_data.get('pricing', 'Unknown'),
            tags        = tool_data.get('tags', ''),
            date_found  = datetime.now(),
        )
        db.add(tool)
        db.commit()
        print(f"  ✅ Saved: {tool_data['name']}")
        return True

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error saving {tool_data['name']}: {e}")
        return False


# ── scraper ───────────────────────────────────────────────────────────────────

def scrape_product_hunt():
    """
    Scrape AI marketing tools from Product Hunt using their public API
    """
    print("\n🚀 Starting Product Hunt scraper...")
    print("=" * 50)

    # Product Hunt public GraphQL API
    url = "https://api.producthunt.com/v2/api/graphql"

    # We use the public token (no auth needed for basic queries)
    PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN")

    headers = {
        "Content-Type" : "application/json",
        "User-Agent"   : "Mozilla/5.0 (compatible; AI-Trends-Bot/1.0)",
        "Authorization": f"Bearer {PRODUCT_HUNT_TOKEN}",
    }

    # GraphQL query to get today's top posts
    query = """
    {
      posts(order: VOTES, topic: "artificial-intelligence", first: 50) {
        edges {
          node {
            id
            name
            tagline
            description
            url
            website
            votesCount
            commentsCount
            createdAt
            topics {
              edges {
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """

    try:
        print("📡 Connecting to Product Hunt API...")
        response = requests.post(
            url,
            headers = headers,
            json    = {"query": query},
            timeout = 30,
        )

        print(f"📊 Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            print("Switching to backup method...")
            return scrape_product_hunt_backup()

        data = response.json()

        # Check if we got valid data
        if 'errors' in data:
            print(f"❌ GraphQL error: {data['errors']}")
            print("Switching to backup method...")
            return scrape_product_hunt_backup()

        # Extract posts
        posts = data.get('data', {}).get('posts', {}).get('edges', [])
        print(f"✅ Found {len(posts)} posts from Product Hunt")

        if not posts:
            print("No posts found, switching to backup...")
            return scrape_product_hunt_backup()

        # Process and save each post
        db      = SessionLocal()
        saved   = 0
        skipped = 0

        # AI marketing keywords to filter relevant tools
        ai_marketing_keywords = [
            'ai', 'marketing', 'seo', 'content', 'social media',
            'email', 'ads', 'copywriting', 'automation', 'analytics',
            'landing page', 'video', 'ugc', 'outreach', 'chatbot',
            'writing', 'copy', 'design', 'campaign', 'lead'
        ]

        print("\n📝 Processing tools...")

        for edge in posts:
            node = edge.get('node', {})

            name        = node.get('name', '')
            tagline     = node.get('tagline', '')
            description = node.get('description', '') or tagline
            website     = node.get('website', '')
            source_url  = node.get('url', '')
            votes       = node.get('votesCount', 0)
            comments    = node.get('commentsCount', 0)

            # Get topics/tags
            topics      = node.get('topics', {}).get('edges', [])
            tags        = ', '.join([t['node']['name'] for t in topics])

            # Filter: only save if relevant to AI marketing
            combined_text = f"{name} {tagline} {tags}".lower()
            is_relevant   = any(
                keyword in combined_text
                for keyword in ai_marketing_keywords
            )

            if not is_relevant:
                skipped += 1
                continue

            # Determine category
            category = determine_category(combined_text)

            tool_data = {
                'name'       : name,
                'description': description,
                'website_url': website,
                'source_url' : source_url,
                'category'   : category,
                'pricing'    : 'Check website',
                'tags'       : tags,
            }

            if save_tool(db, tool_data):
                saved += 1

        db.close()

        print("\n" + "=" * 50)
        print(f"✅ Scraping complete!")
        print(f"   Saved  : {saved} tools")
        print(f"   Skipped: {skipped} irrelevant")
        print("=" * 50)

        return saved

    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet")
        return 0
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 0


def determine_category(text: str) -> str:
    """Determine the category of a tool based on its description"""
    if any(w in text for w in ['seo', 'search', 'keyword', 'ranking']):
        return 'AI SEO Tools'
    elif any(w in text for w in ['video', 'ugc', 'reel', 'tiktok']):
        return 'AI UGC Video Tools'
    elif any(w in text for w in ['social media', 'instagram', 'twitter', 'linkedin']):
        return 'AI Social Media Tools'
    elif any(w in text for w in ['email', 'newsletter', 'inbox']):
        return 'AI Email Marketing Tools'
    elif any(w in text for w in ['ad', 'ads', 'creative', 'banner']):
        return 'AI Ad Creative Tools'
    elif any(w in text for w in ['copy', 'writing', 'content', 'blog']):
        return 'AI Copywriting Tools'
    elif any(w in text for w in ['landing page', 'conversion', 'cro']):
        return 'AI Landing Page Tools'
    elif any(w in text for w in ['analytics', 'data', 'insight', 'report']):
        return 'AI Analytics Tools'
    elif any(w in text for w in ['outreach', 'cold', 'sales', 'lead']):
        return 'AI Cold Outreach Tools'
    else:
        return 'AI Marketing Automation Tools'


def scrape_product_hunt_backup():
    """
    Backup method: use sample data to test database saving
    This runs if the API is not accessible
    """
    print("\n🔄 Running backup method with sample AI tools...")

    sample_tools = [
        {
            'name'       : 'Jasper AI',
            'description': 'AI writing assistant for marketing teams',
            'website_url': 'https://jasper.ai',
            'source_url' : 'https://producthunt.com',
            'category'   : 'AI Copywriting Tools',
            'pricing'    : 'Paid',
            'tags'       : 'AI, Writing, Marketing, Content',
        },
        {
            'name'       : 'Surfer SEO',
            'description': 'AI-powered SEO content optimization tool',
            'website_url': 'https://surferseo.com',
            'source_url' : 'https://producthunt.com',
            'category'   : 'AI SEO Tools',
            'pricing'    : 'Paid',
            'tags'       : 'AI, SEO, Content, Marketing',
        },
        {
            'name'       : 'AdCreative AI',
            'description': 'Generate high-converting ad creatives using AI',
            'website_url': 'https://adcreative.ai',
            'source_url' : 'https://producthunt.com',
            'category'   : 'AI Ad Creative Tools',
            'pricing'    : 'Paid',
            'tags'       : 'AI, Ads, Creative, Marketing',
        },
        {
            'name'       : 'Lately AI',
            'description': 'AI social media content repurposing tool',
            'website_url': 'https://lately.ai',
            'source_url' : 'https://producthunt.com',
            'category'   : 'AI Social Media Tools',
            'pricing'    : 'Paid',
            'tags'       : 'AI, Social Media, Content',
        },
        {
            'name'       : 'Seventh Sense',
            'description': 'AI email marketing optimization platform',
            'website_url': 'https://theseventhsense.com',
            'source_url' : 'https://producthunt.com',
            'category'   : 'AI Email Marketing Tools',
            'pricing'    : 'Paid',
            'tags'       : 'AI, Email, Marketing',
        },
    ]

    db    = SessionLocal()
    saved = 0

    for tool_data in sample_tools:
        if save_tool(db, tool_data):
            saved += 1

    db.close()

    print(f"\n✅ Backup complete! Saved {saved} sample tools")
    return saved


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    scrape_product_hunt()