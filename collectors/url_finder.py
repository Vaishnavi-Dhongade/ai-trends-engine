import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import requests
from googlesearch import search
from config.database import SessionLocal
from models.models import Tool

# ── domains to skip ───────────────────────────────────────────────────────────

SKIP_DOMAINS = [
    'producthunt.com',
    'reddit.com',
    'twitter.com',
    'linkedin.com',
    'facebook.com',
    'youtube.com',
    'wikipedia.org',
    'g2.com',
    'capterra.com',
    'trustpilot.com',
    'appsumo.com',
    'techcrunch.com',
    'forbes.com',
    'medium.com',
    'wordpress.com',
]


def is_valid_url(url: str) -> bool:
    """Check if URL is a valid official website"""
    if not url:
        return False
    for domain in SKIP_DOMAINS:
        if domain in url:
            return False
    return True


def find_website_url(tool_name: str) -> str:
    """
    Search Google to find official website for a tool
    Returns the first valid URL found
    """
    try:
        query = f"{tool_name} official website"
        print(f"    Searching: {query}")

        results = list(search(query, num_results=5, sleep_interval=2))

        for url in results:
            if is_valid_url(url):
                print(f"    Found: {url}")
                return url

        print(f"    No valid URL found")
        return ""

    except Exception as e:
        print(f"    Search error: {e}")
        return ""


def update_tool_urls():
    """Find and update website URLs for all tools"""

    print("\nStarting URL Finder...")
    print("=" * 50)

    db    = SessionLocal()
    tools = db.query(Tool).all()

    print(f"Found {len(tools)} tools to process\n")

    updated = 0
    skipped = 0

    for tool in tools:
        print(f"\nProcessing: {tool.name}")

        # Skip if already has a valid URL
        if tool.website_url and is_valid_url(tool.website_url):
            print(f"    Already has URL: {tool.website_url}")
            skipped += 1
            continue

        # Find URL
        url = find_website_url(tool.name)

        if url:
            tool.website_url = url
            db.commit()
            print(f"    Updated in database!")
            updated += 1
        else:
            skipped += 1

        # Wait between searches to avoid blocking
        print(f"    Waiting 5 seconds...")
        time.sleep(5)

    db.close()

    print("\n" + "=" * 50)
    print(f"URL Finder Complete!")
    print(f"Updated : {updated}")
    print(f"Skipped : {skipped}")
    print("=" * 50)


if __name__ == "__main__":
    update_tool_urls()