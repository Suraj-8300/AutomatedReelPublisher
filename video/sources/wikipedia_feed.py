"""
Free Wikipedia & Wikimedia content feed for AutoReelStudio.
Provides science, tech, news, and mechanical topics — no API key required.
"""

import json
import datetime
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

USER_AGENT = "AutoReelStudio/2.0 (github.com/Suraj-8300/AutoReelStudio)"

HEADERS = {"User-Agent": USER_AGENT}

SCIENCE_CATEGORIES = [
    "Portal:Science", "Portal:Technology", "Portal:Engineering",
    "Portal:Physics", "Portal:Astronomy", "Portal:Medicine",
    "Portal:Biology", "Portal:Chemistry", "Portal:Space",
]


def _get(url: str, timeout: int = 10) -> Optional[Dict]:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


class WikipediaFeed:
    """Fetches free, fresh science and news topics from Wikipedia/Wikimedia APIs."""

    @staticmethod
    def get_trending_topics(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Returns the most-read Wikipedia articles from yesterday.
        These spike on major science, tech, or news events.
        """
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        y, m, d = yesterday.strftime("%Y"), yesterday.strftime("%m"), yesterday.strftime("%d")
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
            f"en.wikipedia/all-access/{y}/{m}/{d}"
        )
        data = _get(url)
        topics = []
        if data:
            articles = data.get("items", [{}])[0].get("articles", [])
            # Filter out meta pages
            skip = {"Main_Page", "Special:", "Wikipedia:", "File:", "Portal:", "Template:"}
            for a in articles:
                title = a.get("article", "")
                if any(title.startswith(s) for s in skip):
                    continue
                topics.append({
                    "title": title.replace("_", " "),
                    "views": a.get("views", 0),
                    "source": "wikipedia_trending",
                })
                if len(topics) >= limit:
                    break
        return topics

    @staticmethod
    def get_featured_article() -> Optional[Dict[str, Any]]:
        """
        Returns today's Wikipedia Featured Article with summary.
        Always a high-quality, well-sourced topic.
        """
        today = datetime.datetime.utcnow()
        y, m, d = today.strftime("%Y"), today.strftime("%m"), today.strftime("%d")
        url = f"https://en.wikipedia.org/api/rest_v1/feed/featured/{y}/{m}/{d}"
        data = _get(url)
        if not data:
            return None
        tfa = data.get("tfa", {})
        return {
            "title": tfa.get("normalizedtitle", tfa.get("title", "")),
            "summary": tfa.get("extract", ""),
            "source": "wikipedia_featured",
        }

    @staticmethod
    def get_article_summary(title: str) -> Optional[Dict[str, Any]]:
        """
        Returns a Wikipedia article summary for a given topic title.
        """
        encoded = urllib.parse.quote(title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        data = _get(url)
        if not data or data.get("type") == "disambiguation":
            return None
        return {
            "title": data.get("title", title),
            "summary": data.get("extract", ""),
            "description": data.get("description", ""),
            "source": "wikipedia_summary",
        }

    @staticmethod
    def get_on_this_day() -> List[Dict[str, Any]]:
        """
        Returns historical science/tech events that happened on today's date.
        Great for evergreen educational content.
        """
        today = datetime.datetime.utcnow()
        m, d = today.strftime("%m"), today.strftime("%d")
        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{m}/{d}"
        data = _get(url)
        if not data:
            return []
        events = []
        for ev in data.get("events", [])[:10]:
            pages = ev.get("pages", [{}])
            if pages:
                p = pages[0]
                events.append({
                    "title": f"{ev.get('year', '')}: {p.get('normalizedtitle', ev.get('text', '')[:80])}",
                    "summary": ev.get("text", ""),
                    "source": "wikipedia_on_this_day",
                })
        return events

    @classmethod
    def get_fresh_topics(cls, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Aggregates trending + featured + on-this-day topics into one fresh pool.
        """
        topics = []
        try:
            topics.extend(cls.get_trending_topics(limit=10))
        except Exception:
            pass
        try:
            featured = cls.get_featured_article()
            if featured:
                topics.append(featured)
        except Exception:
            pass
        try:
            topics.extend(cls.get_on_this_day()[:5])
        except Exception:
            pass
        return topics[:limit]
