import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

FEEDS = {
    "Мир": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Экономика": "https://feeds.bbci.co.uk/news/business/rss.xml",
}
items = []
for category, url in FEEDS.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NewsDashboard/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            root = ET.fromstring(response.read())
        for item in root.findall("./channel/item")[:12]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            date = item.findtext("pubDate", "").strip()
            if title and link:
                items.append({"category": category, "title": title, "url": link, "published": date})
    except Exception as exc:
        print(f"Feed unavailable: {category}: {exc}")
if not items:
    raise SystemExit("No feeds available; existing news.json retained.")
Path("news.json").write_text(json.dumps({
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "items": items
}, ensure_ascii=False, indent=2), encoding="utf-8")
