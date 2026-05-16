import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordpress.publisher import test_connection, publish_tool
from config.database import SessionLocal
from models.models import Tool

print("Publishing all tools to WordPress...")
print("=" * 50)

if test_connection():
    db    = SessionLocal()
    tools = db.query(Tool).all()

    print(f"Found {len(tools)} tools to publish\n")

    saved  = 0
    failed = 0

    for tool in tools:
        if publish_tool(tool):
            saved += 1
        else:
            failed += 1

    db.close()

    print("=" * 50)
    print(f"Done!")
    print(f"Published : {saved}")
    print(f"Failed    : {failed}")
else:
    print("Cannot connect to WordPress. Check .env file.")