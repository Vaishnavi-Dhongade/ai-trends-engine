import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from dotenv import load_dotenv
from config.database import SessionLocal
from models.models import Trend
import json
import time

load_dotenv()

# ── groq client ───────────────────────────────────────────────────────────────

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── content generator ─────────────────────────────────────────────────────────

def generate_trend_content(keyword: str, category: str) -> dict:
    """
    Use Groq AI to generate full content for a trend
    Returns a dictionary with all generated fields
    """

    print(f"    🤖 Generating content for: {keyword}")

    prompt = f"""
You are an expert AI marketing analyst. Generate professional content for this trending topic.

Trend Keyword: {keyword}
Category: {category}

Generate a JSON response with exactly these fields:
{{
    "title": "An engaging title for this trend (max 60 chars)",
    "summary": "A 2-3 sentence summary of this trend and why it matters for marketers",
    "why_growing": "2-3 sentences explaining why this trend is growing right now",
    "use_cases": ["use case 1", "use case 2", "use case 3", "use case 4", "use case 5"],
    "seo_title": "SEO optimized title with keyword (max 60 chars)",
    "meta_description": "SEO meta description (max 155 chars)",
    "excerpt": "Short WordPress excerpt (max 50 words)"
}}

Rules:
- Write for marketing professionals
- Be specific and actionable
- Focus on AI marketing angle
- Return ONLY the JSON, no other text
"""

    try:
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [
                {
                    "role"   : "system",
                    "content": "You are an AI marketing expert. Always respond with valid JSON only."
                },
                {
                    "role"   : "user",
                    "content": prompt
                }
            ],
            temperature = 0.7,
            max_tokens  = 1000,
        )

        # Get response text
        content = response.choices[0].message.content.strip()

        # Clean up response (remove markdown if present)
        content = content.replace("```json", "").replace("```", "").strip()

        # Parse JSON
        data = json.loads(content)
        print(f"    ✅ Content generated successfully!")
        return data

    except json.JSONDecodeError as e:
        print(f"    ❌ JSON parsing error: {e}")
        return get_fallback_content(keyword, category)

    except Exception as e:
        print(f"    ❌ Groq API error: {e}")
        return get_fallback_content(keyword, category)


def get_fallback_content(keyword: str, category: str) -> dict:
    """Fallback content if AI fails"""
    return {
        "title"           : f"{keyword.title()} — Emerging AI Marketing Trend",
        "summary"         : f"{keyword.title()} is an emerging trend in {category} that is gaining traction among marketing professionals.",
        "why_growing"     : f"Marketers are adopting {keyword} tools to save time and improve campaign performance.",
        "use_cases"       : [
            f"Automate {keyword} tasks",
            f"Improve campaign performance",
            f"Save time on manual work",
            f"Scale marketing operations",
            f"Generate better results",
        ],
        "seo_title"       : f"{keyword.title()} Tools — Complete Guide 2026",
        "meta_description": f"Discover the best {keyword} tools and strategies for marketers in 2026.",
        "excerpt"         : f"Learn how {keyword} is transforming marketing in 2026.",
    }


# ── save to database ──────────────────────────────────────────────────────────

def save_content_to_trend(db, trend: Trend, content: dict) -> bool:
    """Save generated content back to trend in database"""
    try:
        trend.summary = content.get('summary', trend.summary)
        db.commit()
        print(f"    💾 Content saved to database!")
        return True
    except Exception as e:
        db.rollback()
        print(f"    ❌ Error saving content: {e}")
        return False


# ── main function ─────────────────────────────────────────────────────────────

def enrich_all_trends():
    """Generate AI content for all trends in database"""

    print("\n🤖 Starting AI Content Generator...")
    print("=" * 50)

    db     = SessionLocal()
    trends = db.query(Trend).all()

    if not trends:
        print("❌ No trends found in database!")
        db.close()
        return

    print(f"📋 Found {len(trends)} trends to enrich\n")

    all_content = {}

    for trend in trends:
        print(f"\n📌 Processing: {trend.keyword}")

        # Generate content
        content = generate_trend_content(trend.keyword, trend.category)

        # Save summary to database
        save_content_to_trend(db, trend, content)

        # Store full content for display
        all_content[trend.keyword] = content

        # Wait between requests
        print(f"    ⏳ Waiting 2 seconds...")
        time.sleep(2)

    db.close()

    # Display results
    print("\n" + "=" * 50)
    print("✅ AI Content Generation Complete!")
    print("=" * 50)

    for keyword, content in all_content.items():
        print(f"\n{'='*50}")
        print(f"📌 TREND: {keyword.upper()}")
        print(f"{'='*50}")
        print(f"Title          : {content.get('title', '')}")
        print(f"Summary        : {content.get('summary', '')}")
        print(f"Why Growing    : {content.get('why_growing', '')}")
        print(f"SEO Title      : {content.get('seo_title', '')}")
        print(f"Meta Desc      : {content.get('meta_description', '')}")
        print(f"Use Cases      :")
        for uc in content.get('use_cases', []):
            print(f"  → {uc}")

    return all_content


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    enrich_all_trends()