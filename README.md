# Violatte Reddit reader

A small, **read-only** tool that lists new public posts in five TikTok Shop subreddits (r/TikTokShop, r/TikTokShopSellers, r/TiktokShopViolations, r/TikTokShopAffiliates, r/TikTokShopAffiliate) that mention TikTok Shop violations or appeals, so a person at [Violatte](https://violatte.com) can decide whether a helpful reply is worth writing.

- **Read-only.** It uses Reddit's application-only OAuth, which can't post, comment, vote or message. Every reply on Reddit is written and posted by a person.
- **Narrow scope.** Five subreddits, one `new` listing each per run. A run every 15 minutes is about 480 API calls a day.
- **Minimal data.** It stores the post id, title, link, time and the first 500 characters of the post text, with no usernames. Entries are deleted after 30 days, or right away when the post is removed on Reddit.
- **No reuse of the data.** It is not sold, shared, used for ads, or used to train AI/ML models.
- **Credentials** come from environment variables and are never committed.

Run it with `REDDIT_CLIENT_ID=… REDDIT_CLIENT_SECRET=… python3 reader.py`. It needs only the Python 3 standard library.

Contact: heyviolatte@gmail.com · Reddit: u/heyviolatte
