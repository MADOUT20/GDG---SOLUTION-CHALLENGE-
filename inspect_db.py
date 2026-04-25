"""Check column names by selecting specific columns."""
import requests

URL = "https://scorquajwibcilceutnx.supabase.co"
KEY = "sb_publishable_xLdUq8mudLRS96Vdjy4CZw_wxXlY3YB"

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
}

TABLES = ["regions", "reports", "donations", "deployments", "data_sources", "activity_logs"]

for t in TABLES:
    r = requests.get(f"{URL}/rest/v1/{t}?select=*&limit=1", headers=headers, timeout=15)
    print(f"\n[{t}] status={r.status_code}")
    try:
        data = r.json()
        if isinstance(data, list) and data:
            print(f"  columns: {list(data[0].keys())}")
        else:
            print(f"  response: {str(data)[:200]}")
    except:
        print(f"  raw: {r.text[:200]}")
