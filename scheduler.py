import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import schedule
import time
from datetime import datetime

def run_collectors():
    print(f"\n{'='*50}")
    print(f"Running daily collection: {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*50}")

    # Run Product Hunt scraper
    print("\n[1/3] Running Product Hunt scraper...")
    from collectors.product_hunt import scrape_product_hunt
    scrape_product_hunt()

    # Run Reddit scraper
    print("\n[2/3] Running Reddit scraper...")
    from collectors.reddit_scraper import scrape_reddit
    scrape_reddit()

    # Run trend scorer
    print("\n[3/3] Running trend scorer...")
    from scoring.trend_scorer import score_all_trends
    score_all_trends()

    print(f"\n{'='*50}")
    print(f"Daily collection complete: {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*50}")


if __name__ == "__main__":
    print("Scheduler started...")
    print("Will run every day at 9:00 AM")
    print("Press Ctrl+C to stop\n")

    # Run immediately when started
    print("Running initial collection now...")
    run_collectors()

    # Then schedule daily at 9 AM
    schedule.every().day.at("09:00").do(run_collectors)

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)