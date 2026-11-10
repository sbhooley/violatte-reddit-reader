#!/usr/bin/env python3
"""Violatte Reddit reader: read-only list of new TikTok Shop violation questions for human review.

What it does
  Every run, it fetches the newest public posts in a fixed list of subreddits (SUBREDDITS) through
  Reddit's official Data API, keeps the ones that mention violations or appeals (KEYWORDS), and writes
  them to a private local queue (queue.jsonl) for Violatte staff to read.

What it never does
  - No posting, commenting, voting, messaging or any other write action. It uses application-only
    OAuth (client credentials), which only works for read-only access, so it can't act as a user.
  - No redistribution, resale, ads targeting or AI/ML training on Reddit data.
  - No user profiling. It stores only the post id, subreddit, title, permalink, created time and the
    first 500 characters of the post text. No author names.
  - Queue entries are deleted after RETENTION_DAYS, and a post deleted on Reddit is dropped on the
    next run.

Limits
  One listing call per subreddit per run (5). Run every 15 minutes (480 calls/day), far below Reddit's published limits.
  Honors the X-Ratelimit-* headers and backs off on 429.

Credentials
  Read from REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET (environment), issued by Reddit after approval.
  Never committed to this repository.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from base64 import b64encode
from pathlib import Path

SUBREDDITS = ("TikTokShop", "TikTokShopSellers", "TiktokShopViolations", "TikTokShopAffiliates", "TikTokShopAffiliate")
KEYWORDS = re.compile(r"violation|appeal|strike|banned|suspend|deactivat|policy|flagged|removed|"
                      r"health rating|account standing|ineligible|withheld|frozen", re.I)
USER_AGENT = "python:com.violatte.reader:v0.1 (by /u/heyviolatte)"
UNFILTERED = {"TiktokShopViolations"}  # every post there is about violations
RETENTION_DAYS = 30
QUEUE = Path(__file__).with_name("queue.jsonl")


def token(client_id, secret):
    """Application-only OAuth token (read-only; cannot post or act as a user)."""
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": "Basic " + b64encode(f"{client_id}:{secret}".encode()).decode(),
                 "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["access_token"]


def get(path, tok):
    req = urllib.request.Request("https://oauth.reddit.com" + path,
                                 headers={"Authorization": f"Bearer {tok}", "User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                remaining = float(r.headers.get("X-Ratelimit-Remaining", "100"))
                if remaining < 5:
                    time.sleep(float(r.headers.get("X-Ratelimit-Reset", "60")))
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(60 * (attempt + 1))
                continue
            raise
    return {}


def load():
    if not QUEUE.exists():
        return {}
    items = (json.loads(line) for line in QUEUE.read_text().splitlines() if line.strip())
    return {i["id"]: i for i in items}


def run():
    tok = token(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"])
    queue, cutoff = load(), time.time() - RETENTION_DAYS * 86400
    for sub in SUBREDDITS:
        listing = get(f"/r/{sub}/new?limit=50&raw_json=1", tok)
        for child in listing.get("data", {}).get("children", []):
            p = child["data"]
            if p.get("removed_by_category") or p.get("selftext") in ("[deleted]", "[removed]"):
                queue.pop(p["id"], None)
                continue
            if p["id"] in queue or (sub not in UNFILTERED and not KEYWORDS.search(p.get("title", "") + " " + p.get("selftext", ""))):
                continue
            queue[p["id"]] = {"id": p["id"], "subreddit": sub, "title": p["title"],
                              "url": "https://www.reddit.com" + p["permalink"],
                              "created": p["created_utc"], "text": p.get("selftext", "")[:500],
                              "status": "new"}
    kept = [i for i in queue.values() if i["created"] >= cutoff]
    QUEUE.write_text("".join(json.dumps(i) + "\n" for i in sorted(kept, key=lambda i: i["created"])))
    print(f"{len(kept)} items in queue")


if __name__ == "__main__":
    sys.exit(run())
