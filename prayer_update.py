
import os
import json
import hashlib
import re
import html
from datetime import datetime, timezone

import feedparser
from google.cloud import firestore
from google.oauth2 import service_account


FEEDS = [
    {
        "category": "ప్రపంచం",
        "url": "https://www.thehindu.com/news/international/feeder/default.rss"
    },
    {
        "category": "భారతదేశం",
        "url": "https://www.thehindu.com/news/national/feeder/default.rss"
    },
    {
        "category": "ఆంధ్రప్రదేశ్",
        "url": "https://www.thehindu.com/news/national/andhra-pradesh/feeder/default.rss"
    },
    {
        "category": "తెలంగాణ",
        "url": "https://www.thehindu.com/news/national/telangana/feeder/default.rss"
    },
    {
        "category": "ఇతర రాష్ట్రాలు",
        "url": "https://www.thehindu.com/news/states/feeder/default.rss"
    }
]


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return " ".join(value.split())[:2000]


def main():
    secret_text = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not secret_text:
        raise RuntimeError("Firebase secret is missing")

    service_info = json.loads(secret_text)

    credentials = service_account.Credentials.from_service_account_info(
        service_info
    )

    db = firestore.Client(
        project=service_info["project_id"],
        credentials=credentials
    )

    collection = db.collection("autoPrayerPoints")
    batch = db.batch()
    count = 0

    for feed in FEEDS:
        print("Reading:", feed["category"])

        parsed = feedparser.parse(feed["url"])

        for entry in parsed.entries[:20]:
            title = clean_text(entry.get("title", ""))
            link = entry.get("link", "")

            if not title or not link:
                continue

            summary = clean_text(entry.get("summary", ""))

            doc_id = hashlib.sha256(
                link.encode("utf-8")
            ).hexdigest()

            document = {
                "category": feed["category"],
                "title": title,
                "summary": summary,
                "source": "The Hindu",
                "sourceUrl": link,
                "published": entry.get("published", ""),
                "reviewStatus": "pending_review",
                "prayerText": "",
                "fetchedAt": datetime.now(timezone.utc)
            }

            batch.set(collection.document(doc_id), document)
            count += 1

    if count:
        batch.commit()

    print("Collected articles:", count)
    print("Saved to Firestore autoPrayerPoints")


if __name__ == "__main__":
    main()
  
