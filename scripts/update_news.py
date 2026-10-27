#!/usr/bin/env python3
"""Обновление русскоязычных новостей для GitHub Pages. Без внешних библиотек."""
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# Google News RSS: поисковые ленты с русскоязычной локализацией.
QUERIES = {
    "Недвижимость Москвы и МО": 'новостройки Москва Московская область застройщики',
    "Девелоперы и продажи": 'девелоперы продажи квартир ипотека новостройки',
    "Экономика России": 'ключевая ставка инфляция экономика России',
    "Ипотека и регулирование": 'семейная ипотека Минстрой ЦБ недвижимость',
    "Мировая экономика": 'мировая экономика финансовые рынки',
}
PER_FEED = 15
MAX_ITEMS = 70

def clean(value):
    value = re.sub(r"<[^>]*>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def rss_url(query):
    return ("https://news.google.com/rss/search?q="
            + urllib.parse.quote(query)
            + "&hl=ru&gl=RU&ceid=RU:ru")

def read_feed(category, query):
    request = urllib.request.Request(
        rss_url(query),
        headers={"User-Agent": "Mozilla/5.0 (compatible; NewsPortal/1.0)"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    found = []
    for entry in root.findall("./channel/item")[:PER_FEED]:
        title = clean(entry.findtext("title"))
        link = (entry.findtext("link") or "").strip()
        published = (entry.findtext("pubDate") or "").strip()
        source_node = entry.find("source")
        source = clean(source_node.text if source_node is not None else "")
        description = clean(entry.findtext("description"))
        if not title or not link.startswith("https://"):
            continue
        # В Google News заголовок иногда заканчивается названием издания.
        if source and title.endswith(" - " + source):
            title = title[:-(len(source) + 3)]
        found.append({
            "category": category,
            "title": title,
            "url": link,
            "published": published,
            "source": source,
            "description": description[:350],
        })
    return found

def date_key(item):
    try:
        return parsedate_to_datetime(item["published"]).timestamp()
    except (ValueError, TypeError, OverflowError):
        return 0

def main():
    articles = []
    for category, query in QUERIES.items():
        try:
            result = read_feed(category, query)
            print(f"{category}: {len(result)}")
            articles.extend(result)
        except Exception as exc:
            print(f"Источник недоступен ({category}): {exc}")

    unique = {}
    for item in articles:
        key = re.sub(r"\W+", "", item["title"].casefold())
        if key and key not in unique:
            unique[key] = item

    result = sorted(unique.values(), key=date_key, reverse=True)[:MAX_ITEMS]
    if not result:
        raise SystemExit("Нет доступных новостей. Старый news.json сохранён.")

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": result,
    }
    Path("news.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Сохранено новостей: {len(result)}")

if __name__ == "__main__":
    main()
