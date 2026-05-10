import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import re
from datetime import datetime
from config.database import SessionLocal
from models.models import Tool, Trend

# ── helpers ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text.strip('-')


def is_duplicate_tool(db, name: str) -> bool:
    return db.query(Tool).filter(Tool.name == name).first() is not None


def is_duplicate_trend(db, keyword: str) -> bool:
    return db.query(Trend).filter(Trend.keyword == keyword).first() is not None


def determine_category(text: str) -> str:
    text = text.lower()
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


# ── reddit fetcher ────────────────────────────────────────────────────────────

def fetch_subreddit(subreddit: str, limit: int = 25) -> list:
    """Fetch posts from a subreddit using public JSON endpoint"""

    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Trends-Bot/1.0"
    }

    try:
        print(f"  📡 Fetching r/{subreddit}...")
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            data     = response.json()
            posts    = data.get('data', {}).get('children', [])
            print(f"  ✅ Got {len(posts)} posts from r/{subreddit}")
            return posts
        else:
            print(f"  ❌ Error {response.status_code} for r/{subreddit}")
            return []

    except Exception as e:
        print(f"  ❌ Failed to fetch r/{subreddit}: {e}")
        return []


# ── keyword extractor ─────────────────────────────────────────────────────────

def extract_trends_from_posts(posts: list, subreddit: str) -> list:
    """Extract trending keywords from Reddit posts"""

    # AI marketing keywords to look for
    trend_keywords = [
        'ai seo', 'ai content', 'ai marketing', 'ai copywriting',
        'ai ads', 'ai email', 'ai social media', 'ai analytics',
        'ai automation', 'ai landing page', 'ai video', 'ai ugc',
        'chatgpt marketing', 'claude marketing', 'gemini marketing',
        'ai lead generation', 'ai outreach', 'ai cold email',
        'generative ai marketing', 'ai influencer', 'ai personalization',
        'prompt engineering marketing', 'ai a/b testing',
        'ai campaign', 'ai creative', 'ai targeting'
    ]

    found_trends = []

    for post in posts:
        data  = post.get('data', {})
        title = data.get('title', '').lower()
        text  = data.get('selftext', '').lower()
        combined = f"{title} {text}"

        for keyword in trend_keywords:
            if keyword in combined:
                found_trends.append({
                    'keyword'   : keyword,
                    'slug'      : slugify(keyword),
                    'category'  : determine_category(keyword),
                    'summary'   : f"Trending discussion about {keyword} found on r/{subreddit}",
                    'source'    : subreddit,
                    'post_title': data.get('title', ''),
                    'upvotes'   : data.get('ups', 0),
                })

    return found_trends


# ── tool extractor ────────────────────────────────────────────────────────────

def extract_tools_from_posts(posts: list, subreddit: str) -> list:
    """Extract AI tool mentions from Reddit posts"""

    # Common AI marketing tools to detect
    known_tools = [
        'jasper', 'copy.ai', 'writesonic', 'surfer seo', 'semrush',
        'ahrefs', 'clearscope', 'marketmuse', 'frase', 'neuronwriter',
        'adcreative', 'pencil', 'smartly', 'albert ai', 'persado',
        'phrasee', 'seventh sense', 'brafton', 'anyword', 'hypotenuse',
        'recently', 'ocoya', 'flick', 'predis', 'hootsuite',
        'sprout social', 'buffer', 'loomly', 'publer', 'missinglettr',
        'klaviyo', 'mailchimp', 'activecampaign', 'convertkit',
        'lemlist', 'instantly', 'apollo', 'outreach', 'salesloft',
        'unbounce', 'instapage', 'leadpages', 'swipe pages',
        'chatgpt', 'claude', 'gemini', 'perplexity', 'midjourney',
        'runway', 'synthesia', 'heygen', 'descript', 'opus clip'
    ]

    found_tools = []

    for post in posts:
        data     = post.get('data', {})
        title    = data.get('title', '').lower()
        text     = data.get('selftext', '').lower()
        combined = f"{title} {text}"

        for tool in known_tools:
            if tool in combined:
                found_tools.append({
                    'name'       : tool.title(),
                    'description': f"AI marketing tool mentioned on r/{subreddit}",
                    'website_url': '',
                    'source_url' : f"https://reddit.com/r/{subreddit}",
                    'category'   : determine_category(tool),
                    'pricing'    : 'Check website',
                    'tags'       : f"reddit, {subreddit}, ai, marketing",
                })

    return found_tools


# ── save functions ────────────────────────────────────────────────────────────

def save_trend(db, trend_data: dict) -> bool:
    try:
        if is_duplicate_trend(db, trend_data['keyword']):
            print(f"    ⚠️  Duplicate trend: {trend_data['keyword']}")
            return False

        trend = Trend(
            keyword  = trend_data['keyword'],
            slug     = trend_data['slug'],
            category = trend_data['category'],
            summary  = trend_data['summary'],
            status   = 'new',
        )
        db.add(trend)
        db.commit()
        print(f"    ✅ Trend saved: {trend_data['keyword']}")
        return True

    except Exception as e:
        db.rollback()
        print(f"    ❌ Error saving trend: {e}")
        return False


def save_tool(db, tool_data: dict) -> bool:
    try:
        if is_duplicate_tool(db, tool_data['name']):
            return False

        tool = Tool(
            name        = tool_data['name'],
            slug        = slugify(tool_data['name']),
            description = tool_data['description'],
            website_url = tool_data['website_url'],
            source_url  = tool_data['source_url'],
            category    = tool_data['category'],
            pricing     = tool_data['pricing'],
            tags        = tool_data['tags'],
            date_found  = datetime.now(),
        )
        db.add(tool)
        db.commit()
        print(f"    ✅ Tool saved: {tool_data['name']}")
        return True

    except Exception as e:
        db.rollback()
        print(f"    ❌ Error saving tool: {e}")
        return False


# ── main scraper ──────────────────────────────────────────────────────────────

def scrape_reddit():
    print("\n🚀 Starting Reddit scraper...")
    print("=" * 50)

    # Subreddits to scrape
    subreddits = [
        'artificial',
        'marketing',
        'SEO',
        'SaaS',
        'digitalmarketing',
        'contentmarketing',
    ]

    db             = SessionLocal()
    total_trends   = 0
    total_tools    = 0

    for subreddit in subreddits:
        print(f"\n📌 Scraping r/{subreddit}...")

        # Fetch posts
        posts = fetch_subreddit(subreddit)

        if not posts:
            continue

        # Extract and save trends
        trends = extract_trends_from_posts(posts, subreddit)
        for trend in trends:
            if save_trend(db, trend):
                total_trends += 1

        # Extract and save tools
        tools = extract_tools_from_posts(posts, subreddit)
        for tool in tools:
            if save_tool(db, tool):
                total_tools += 1

    db.close()

    print("\n" + "=" * 50)
    print(f"✅ Reddit scraping complete!")
    print(f"   Trends saved : {total_trends}")
    print(f"   Tools saved  : {total_tools}")
    print("=" * 50)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    scrape_reddit()