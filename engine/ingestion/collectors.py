"""
JanPulse AI — Data Ingestion Layer
Collectors for all monitored platforms. Each collector publishes to Redis Streams.
"""

import os
import json
import time
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from engine.models import (
    DataPoint, Platform, ContentType, AuthorInfo, EngagementMetrics,
    ContentMetadata, TemporalInfo, GeoInfo, LanguageCode
)


# ─── BASE COLLECTOR ──────────────────────────────────────────────────────

class BaseCollector(ABC):
    """Abstract base class for all platform collectors."""

    def __init__(self, platform: Platform, keywords: list[str], hashtags: list[str],
                 redis_stream=None, campaign_id: str = ""):
        self.platform = platform
        self.keywords = keywords
        self.hashtags = hashtags
        self.redis_stream = redis_stream
        self.campaign_id = campaign_id
        self.collected_count = 0
        self._seen_ids = set()

    def _dedup_id(self, source_id: str) -> bool:
        """Returns True if already seen."""
        h = hashlib.sha256(f"{self.platform.value}:{source_id}".encode()).hexdigest()[:16]
        if h in self._seen_ids:
            return True
        self._seen_ids.add(h)
        if len(self._seen_ids) > 500000:
            # Deterministic eviction: clear oldest half by converting to sorted list
            sorted_ids = sorted(self._seen_ids)
            self._seen_ids = set(sorted_ids[len(sorted_ids) // 2:])
        return False

    def publish(self, datapoint: DataPoint):
        """Publish a data point to the Redis stream."""
        if self.redis_stream:
            self.redis_stream.publish("raw-ingestion", {
                "doc_id": datapoint.doc_id,
                "platform": datapoint.source_platform.value,
                "data": datapoint.model_dump_json()
            })
        self.collected_count += 1

    @abstractmethod
    def collect(self):
        """Run one collection cycle."""
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Verify API credentials are valid."""
        pass


# ─── TWITTER / X COLLECTOR ───────────────────────────────────────────────

class TwitterCollector(BaseCollector):
    """
    Collects from X/Twitter API v2.
    Supports: Filtered stream (real-time), Recent search (polling).
    """

    def __init__(self, keywords, hashtags, redis_stream=None, campaign_id=""):
        super().__init__(Platform.TWITTER, keywords, hashtags, redis_stream, campaign_id)
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.client = None
        self._setup_client()

    def _setup_client(self):
        try:
            import tweepy
            if self.bearer_token:
                self.client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    wait_on_rate_limit=True
                )
                logger.info("Twitter API v2 client initialised")
            else:
                logger.warning("No Twitter bearer token; running in demo mode")
        except ImportError:
            logger.warning("tweepy not installed")

    def validate_credentials(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.get_me()
            return True
        except Exception:
            return False

    def _build_query(self) -> str:
        """Build Twitter API v2 search query from keywords and hashtags."""
        parts = []
        if self.keywords:
            kw_part = " OR ".join(f'"{k}"' if " " in k else k for k in self.keywords[:25])
            parts.append(f"({kw_part})")
        if self.hashtags:
            ht_part = " OR ".join(self.hashtags[:10])
            parts.append(f"({ht_part})")
        query = " OR ".join(parts)
        query += " -is:retweet lang:en OR lang:hi OR lang:bn"
        return query[:1024]  # API limit

    def collect(self):
        """Run one search cycle and publish results."""
        if not self.client:
            logger.debug("Twitter client not available; generating demo data")
            self._collect_demo()
            return

        try:
            import tweepy
            query = self._build_query()
            response = self.client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=["created_at", "public_metrics", "entities", "lang", "geo", "conversation_id"],
                user_fields=["public_metrics", "location", "verified"],
                expansions=["author_id"]
            )

            if not response.data:
                logger.debug("No tweets found in this cycle")
                return

            users = {u.id: u for u in (response.includes.get("users", []) or [])}

            for tweet in response.data:
                if self._dedup_id(str(tweet.id)):
                    continue

                user = users.get(tweet.author_id)
                metrics = tweet.public_metrics or {}
                entities = tweet.entities or {}

                dp = DataPoint(
                    source_platform=Platform.TWITTER,
                    source_id=str(tweet.id),
                    source_url=f"https://x.com/i/status/{tweet.id}",
                    content_type=ContentType.TEXT,
                    raw_text=tweet.text,
                    language_detected=self._map_lang(tweet.lang),
                    author=AuthorInfo(
                        author_id=str(tweet.author_id),
                        display_name=user.name if user else "",
                        follower_count=user.public_metrics.get("followers_count", 0) if user else 0,
                        verified=user.verified if user else False,
                    ),
                    engagement=EngagementMetrics(
                        likes=metrics.get("like_count", 0),
                        shares=metrics.get("retweet_count", 0),
                        comments=metrics.get("reply_count", 0),
                        views=metrics.get("impression_count", 0),
                    ),
                    metadata=ContentMetadata(
                        hashtags=[h["tag"] for h in entities.get("hashtags", [])],
                        mentions=[m["username"] for m in entities.get("mentions", [])],
                        urls=[u["expanded_url"] for u in entities.get("urls", [])],
                    ),
                    temporal=TemporalInfo(created_at=tweet.created_at or datetime.utcnow()),
                )
                self.publish(dp)

            logger.info(f"Twitter: collected {len(response.data)} tweets")

        except Exception as e:
            logger.error(f"Twitter collection error: {e}")

    def _map_lang(self, lang_code: str) -> LanguageCode:
        mapping = {"en": LanguageCode.ENGLISH, "hi": LanguageCode.HINDI, "bn": LanguageCode.BENGALI}
        return mapping.get(lang_code, LanguageCode.UNKNOWN)

    def _collect_demo(self):
        """Generate demo data for testing without API access."""
        import random
        demo_texts = [
            "Modi rally in Kolkata looks like it will be massive! BJP is going all out #ModiInKolkata",
            "Why is PM Modi wasting time in Bengal? Focus on national issues first #KhelaHobe",
            "Brigade Parade Ground is going to be packed tomorrow. Historic rally incoming!",
            "Didi will show BJP their place. Bengal doesn't need outsiders telling us what to do",
            "कोलकाता में मोदी जी की रैली जबरदस्त होने वाली है! #ModiMegaRally",
            "বিজেপি বাংলায় কিছুই করতে পারবে না। খেলা হবে!",
            "Empty promises again. Same old jumla sarkar. Acche din kab aayenge?",
            "Modi's rally will change Bengal forever. Development is coming! #BJP4Bengal",
            "Modiji er rally te onek lok esechilo. Khub bhalo laglo.",
            "Another election, another rally, another set of broken promises. Waah kya vikas ho raha hai",
        ]
        for i, text in enumerate(demo_texts):
            dp = DataPoint(
                source_platform=Platform.TWITTER,
                source_id=f"demo_tw_{int(time.time())}_{i}",
                content_type=ContentType.TEXT,
                raw_text=text,
                author=AuthorInfo(
                    author_id=f"demo_user_{i}",
                    display_name=f"DemoUser{i}",
                    follower_count=random.randint(50, 50000),
                ),
                engagement=EngagementMetrics(
                    likes=random.randint(0, 500),
                    shares=random.randint(0, 200),
                    comments=random.randint(0, 50),
                ),
                metadata=ContentMetadata(hashtags=random.sample(
                    ["ModiInKolkata", "KhelaHobe", "BJP4Bengal", "BengalElection2026"], k=random.randint(0, 2)
                )),
                temporal=TemporalInfo(created_at=datetime.utcnow() - timedelta(minutes=random.randint(0, 60))),
            )
            self.publish(dp)
        logger.info(f"Twitter DEMO: published {len(demo_texts)} demo tweets")


# ─── YOUTUBE COLLECTOR ───────────────────────────────────────────────────

class YouTubeCollector(BaseCollector):
    """
    Collects from YouTube Data API v3.
    Supports: Video comments, Live chat messages.
    """

    def __init__(self, keywords, hashtags, redis_stream=None, campaign_id=""):
        super().__init__(Platform.YOUTUBE, keywords, hashtags, redis_stream, campaign_id)
        self.api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.service = None
        self._tracked_videos = []
        self._live_chat_ids = {}
        self._setup_client()

    def _setup_client(self):
        try:
            from googleapiclient.discovery import build
            if self.api_key:
                self.service = build("youtube", "v3", developerKey=self.api_key)
                logger.info("YouTube Data API v3 client initialised")
            else:
                logger.warning("No YouTube API key; running in demo mode")
        except ImportError:
            logger.warning("google-api-python-client not installed")

    def validate_credentials(self) -> bool:
        if not self.service:
            return False
        try:
            self.service.videos().list(part="snippet", id="dQw4w9WgXcQ").execute()
            return True
        except Exception:
            return False

    def discover_videos(self, query: str, max_results: int = 10):
        """Find rally-related videos."""
        if not self.service:
            return
        try:
            response = self.service.search().list(
                q=query, part="snippet", type="video",
                maxResults=max_results, order="date",
                publishedAfter=(datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
            ).execute()
            for item in response.get("items", []):
                vid = item["id"]["videoId"]
                if vid not in self._tracked_videos:
                    self._tracked_videos.append(vid)
                    logger.info(f"YouTube: tracking video {vid} - {item['snippet']['title']}")
        except Exception as e:
            logger.error(f"YouTube video discovery error: {e}")

    def collect(self):
        """Collect comments from tracked videos."""
        if not self.service:
            self._collect_demo()
            return

        for video_id in self._tracked_videos:
            try:
                response = self.service.commentThreads().list(
                    part="snippet", videoId=video_id,
                    maxResults=100, order="time"
                ).execute()
                for item in response.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    comment_id = item["id"]
                    if self._dedup_id(comment_id):
                        continue

                    dp = DataPoint(
                        source_platform=Platform.YOUTUBE,
                        source_id=comment_id,
                        source_url=f"https://youtube.com/watch?v={video_id}",
                        content_type=ContentType.COMMENT,
                        raw_text=snippet.get("textDisplay", ""),
                        author=AuthorInfo(
                            author_id=snippet.get("authorChannelId", {}).get("value", ""),
                            display_name=snippet.get("authorDisplayName", ""),
                        ),
                        engagement=EngagementMetrics(likes=snippet.get("likeCount", 0)),
                        temporal=TemporalInfo(
                            created_at=datetime.fromisoformat(
                                snippet.get("publishedAt", "").replace("Z", "+00:00")
                            ) if snippet.get("publishedAt") else datetime.utcnow()
                        ),
                    )
                    self.publish(dp)

                logger.info(f"YouTube: collected comments from video {video_id}")
            except Exception as e:
                logger.error(f"YouTube comment collection error for {video_id}: {e}")

    def collect_live_chat(self, live_chat_id: str):
        """Collect live chat messages during a rally livestream."""
        if not self.service:
            return
        try:
            response = self.service.liveChatMessages().list(
                liveChatId=live_chat_id, part="snippet,authorDetails", maxResults=200
            ).execute()
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                author = item.get("authorDetails", {})
                msg_id = item["id"]
                if self._dedup_id(msg_id):
                    continue

                dp = DataPoint(
                    source_platform=Platform.LIVESTREAM_CHAT,
                    source_id=msg_id,
                    content_type=ContentType.LIVE_CHAT,
                    raw_text=snippet.get("displayMessage", ""),
                    author=AuthorInfo(
                        author_id=author.get("channelId", ""),
                        display_name=author.get("displayName", ""),
                    ),
                    temporal=TemporalInfo(
                        created_at=datetime.fromisoformat(
                            snippet.get("publishedAt", "").replace("Z", "+00:00")
                        ) if snippet.get("publishedAt") else datetime.utcnow()
                    ),
                )
                self.publish(dp)

            logger.info(f"YouTube LiveChat: collected {len(response.get('items', []))} messages")
            return response.get("pollingIntervalMillis", 10000)
        except Exception as e:
            logger.error(f"YouTube live chat error: {e}")
            return 10000

    def _collect_demo(self):
        import random
        demo_comments = [
            "Modi ji is the best PM India has ever had! Kolkata rally will be historic",
            "BJP can never win Bengal. TMC forever. Khela Hobe!",
            "Good speech by PM Modi but where are the jobs he promised?",
            "মোদীজি আমাদের বাংলায় স্বাগত। উন্নয়ন চাই!",
            "Same old promises. Nothing will change for common people.",
        ]
        for i, text in enumerate(demo_comments):
            dp = DataPoint(
                source_platform=Platform.YOUTUBE,
                source_id=f"demo_yt_{int(time.time())}_{i}",
                content_type=ContentType.COMMENT,
                raw_text=text,
                author=AuthorInfo(author_id=f"yt_user_{i}", display_name=f"YouTubeUser{i}"),
                engagement=EngagementMetrics(likes=random.randint(0, 100)),
                temporal=TemporalInfo(created_at=datetime.utcnow()),
            )
            self.publish(dp)
        logger.info("YouTube DEMO: published demo comments")


# ─── REDDIT COLLECTOR ────────────────────────────────────────────────────

class RedditCollector(BaseCollector):
    """Collects from Reddit API via PRAW."""

    def __init__(self, keywords, hashtags, redis_stream=None, campaign_id="",
                 subreddits=None):
        super().__init__(Platform.REDDIT, keywords, hashtags, redis_stream, campaign_id)
        self.subreddits = subreddits or ["india", "kolkata", "IndiaSpeaks", "IndianPolitics"]
        self.client = None
        self._setup_client()

    def _setup_client(self):
        try:
            import praw
            client_id = os.getenv("REDDIT_CLIENT_ID", "")
            client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
            user_agent = os.getenv("REDDIT_USER_AGENT", "RallyIntelligenceEngine/1.0")
            if client_id and client_secret:
                self.client = praw.Reddit(
                    client_id=client_id, client_secret=client_secret,
                    user_agent=user_agent
                )
                logger.info("Reddit PRAW client initialised")
        except ImportError:
            logger.warning("praw not installed")

    def validate_credentials(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.subreddit("india").id
            return True
        except Exception:
            return False

    def collect(self):
        if not self.client:
            self._collect_demo()
            return

        for sub_name in self.subreddits:
            try:
                subreddit = self.client.subreddit(sub_name)
                for submission in subreddit.new(limit=50):
                    if self._dedup_id(submission.id):
                        continue
                    text = f"{submission.title}\n{submission.selftext}" if submission.selftext else submission.title
                    if not any(kw.lower() in text.lower() for kw in self.keywords):
                        continue

                    dp = DataPoint(
                        source_platform=Platform.REDDIT,
                        source_id=submission.id,
                        source_url=f"https://reddit.com{submission.permalink}",
                        content_type=ContentType.TEXT,
                        raw_text=text,
                        author=AuthorInfo(
                            author_id=str(submission.author) if submission.author else "deleted",
                            display_name=str(submission.author) if submission.author else "deleted",
                        ),
                        engagement=EngagementMetrics(
                            likes=submission.score,
                            comments=submission.num_comments,
                        ),
                        temporal=TemporalInfo(
                            created_at=datetime.utcfromtimestamp(submission.created_utc)
                        ),
                    )
                    self.publish(dp)

                    # Also collect top comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:20]:
                        if self._dedup_id(comment.id):
                            continue
                        cdp = DataPoint(
                            source_platform=Platform.REDDIT,
                            source_id=comment.id,
                            source_url=f"https://reddit.com{comment.permalink}",
                            content_type=ContentType.COMMENT,
                            raw_text=comment.body,
                            author=AuthorInfo(
                                author_id=str(comment.author) if comment.author else "deleted",
                            ),
                            engagement=EngagementMetrics(likes=comment.score),
                            metadata=ContentMetadata(parent_id=submission.id),
                            temporal=TemporalInfo(
                                created_at=datetime.utcfromtimestamp(comment.created_utc)
                            ),
                        )
                        self.publish(cdp)

                logger.info(f"Reddit: collected from r/{sub_name}")
            except Exception as e:
                logger.error(f"Reddit collection error for r/{sub_name}: {e}")

    def _collect_demo(self):
        import random
        demo = [
            "What do you guys think about the upcoming Modi rally in Kolkata? Will BJP make inroads?",
            "TMC has Bengal locked down. No amount of rallies will change that.",
            "As a Bengali, I think both parties are terrible. We need better options.",
        ]
        for i, text in enumerate(demo):
            dp = DataPoint(
                source_platform=Platform.REDDIT, source_id=f"demo_rd_{int(time.time())}_{i}",
                content_type=ContentType.TEXT, raw_text=text,
                author=AuthorInfo(author_id=f"reddit_user_{i}"),
                engagement=EngagementMetrics(likes=random.randint(-5, 100), comments=random.randint(0, 30)),
                temporal=TemporalInfo(created_at=datetime.utcnow()),
            )
            self.publish(dp)


# ─── NEWS/RSS COLLECTOR ──────────────────────────────────────────────────

class NewsCollector(BaseCollector):
    """Collects from NewsAPI, RSS feeds, and GDELT."""

    RSS_FEEDS = {
        "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
        "Times of India": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
        "Indian Express": "https://indianexpress.com/section/political-pulse/feed/",
        "ABP Ananda": "https://bengali.abplive.com/rss",
        "Anandabazar": "https://www.anandabazar.com/rss/politics",
    }

    def __init__(self, keywords, hashtags, redis_stream=None, campaign_id=""):
        super().__init__(Platform.NEWS, keywords, hashtags, redis_stream, campaign_id)
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")

    def validate_credentials(self) -> bool:
        return bool(self.newsapi_key)

    def collect(self):
        self._collect_rss()
        if self.newsapi_key:
            self._collect_newsapi()
        self._collect_gdelt()

    def _collect_rss(self):
        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser not installed")
            return

        for source_name, feed_url in self.RSS_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:
                    title = entry.get("title", "")
                    desc = entry.get("summary", "")
                    text = f"{title}. {desc}"

                    if not any(kw.lower() in text.lower() for kw in self.keywords[:10]):
                        continue

                    entry_id = entry.get("id", entry.get("link", ""))
                    if self._dedup_id(entry_id):
                        continue

                    published = entry.get("published_parsed")
                    created_at = datetime(*published[:6]) if published else datetime.utcnow()

                    dp = DataPoint(
                        source_platform=Platform.NEWS,
                        source_id=entry_id,
                        source_url=entry.get("link", ""),
                        content_type=ContentType.HEADLINE,
                        raw_text=text,
                        author=AuthorInfo(author_id=source_name, display_name=source_name),
                        temporal=TemporalInfo(created_at=created_at),
                    )
                    self.publish(dp)

                logger.debug(f"RSS: collected from {source_name}")
            except Exception as e:
                logger.error(f"RSS error for {source_name}: {e}")

    def _collect_newsapi(self):
        import requests
        try:
            query = " OR ".join(self.keywords[:5])
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query, "language": "en", "sortBy": "publishedAt",
                "pageSize": 50, "apiKey": self.newsapi_key
            }
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            for article in data.get("articles", []):
                title = article.get("title", "")
                desc = article.get("description", "")
                aid = article.get("url", "")
                if self._dedup_id(aid):
                    continue
                dp = DataPoint(
                    source_platform=Platform.NEWS,
                    source_id=aid, source_url=aid,
                    content_type=ContentType.HEADLINE,
                    raw_text=f"{title}. {desc}",
                    author=AuthorInfo(
                        author_id=article.get("source", {}).get("id", ""),
                        display_name=article.get("source", {}).get("name", ""),
                    ),
                    temporal=TemporalInfo(
                        created_at=datetime.fromisoformat(
                            article.get("publishedAt", "").replace("Z", "+00:00")
                        ) if article.get("publishedAt") else datetime.utcnow()
                    ),
                )
                self.publish(dp)
            logger.info(f"NewsAPI: collected {len(data.get('articles', []))} articles")
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")

    def _collect_gdelt(self):
        import requests
        try:
            query = " ".join(self.keywords[:3])
            url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&maxrecords=50&format=json"
            resp = requests.get(url, timeout=15)
            data = resp.json()
            for article in data.get("articles", []):
                aid = article.get("url", "")
                if self._dedup_id(aid):
                    continue
                dp = DataPoint(
                    source_platform=Platform.NEWS,
                    source_id=aid, source_url=aid,
                    content_type=ContentType.HEADLINE,
                    raw_text=article.get("title", ""),
                    author=AuthorInfo(
                        author_id=article.get("domain", ""),
                        display_name=article.get("domain", ""),
                    ),
                    temporal=TemporalInfo(created_at=datetime.utcnow()),
                )
                self.publish(dp)
            logger.info(f"GDELT: collected {len(data.get('articles', []))} articles")
        except Exception as e:
            logger.debug(f"GDELT error (non-critical): {e}")


# ─── GOOGLE TRENDS COLLECTOR ─────────────────────────────────────────────

class GoogleTrendsCollector(BaseCollector):
    """Collects search interest data from Google Trends via pytrends."""

    def __init__(self, keywords, hashtags, redis_stream=None, campaign_id=""):
        super().__init__(Platform.GOOGLE_TRENDS, keywords, hashtags, redis_stream, campaign_id)

    def validate_credentials(self) -> bool:
        return True  # No auth needed

    def collect(self):
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl="en-IN", tz=330)

            # Process keywords in batches of 5 (API limit)
            for i in range(0, len(self.keywords[:20]), 5):
                batch = self.keywords[i:i + 5]
                try:
                    pytrends.build_payload(batch, cat=0, timeframe="now 7-d", geo="IN-WB")
                    interest = pytrends.interest_over_time()
                    if interest.empty:
                        continue

                    for kw in batch:
                        if kw in interest.columns:
                            latest_val = float(interest[kw].iloc[-1])
                            avg_val = float(interest[kw].mean())
                            dp = DataPoint(
                                source_platform=Platform.GOOGLE_TRENDS,
                                source_id=f"gtrends_{kw}_{datetime.utcnow().strftime('%Y%m%d%H')}",
                                content_type=ContentType.SEARCH_TREND,
                                raw_text=f"Google Trends: '{kw}' interest={latest_val}, avg_7d={avg_val:.1f}",
                                engagement=EngagementMetrics(views=int(latest_val)),
                                metadata=ContentMetadata(
                                    hashtags=[kw],
                                    geo=GeoInfo(state="West Bengal")
                                ),
                                temporal=TemporalInfo(created_at=datetime.utcnow()),
                            )
                            self.publish(dp)

                    # Regional interest
                    regional = pytrends.interest_by_region(resolution="CITY", inc_low_vol=True)
                    # Store regional data as metadata
                    for city in regional.index[:10]:
                        for kw in batch:
                            if kw in regional.columns and regional.loc[city, kw] > 0:
                                dp = DataPoint(
                                    source_platform=Platform.GOOGLE_TRENDS,
                                    source_id=f"gtrends_geo_{kw}_{city}",
                                    content_type=ContentType.SEARCH_TREND,
                                    raw_text=f"Regional interest: '{kw}' in {city} = {regional.loc[city, kw]}",
                                    metadata=ContentMetadata(
                                        geo=GeoInfo(place_name=city, state="West Bengal")
                                    ),
                                    temporal=TemporalInfo(created_at=datetime.utcnow()),
                                )
                                self.publish(dp)

                    time.sleep(2)  # Rate limit
                except Exception as e:
                    logger.error(f"Google Trends batch error: {e}")
                    time.sleep(5)

            logger.info("Google Trends: collection cycle complete")
        except ImportError:
            logger.warning("pytrends not installed")


# ─── TELEGRAM COLLECTOR ──────────────────────────────────────────────────

class TelegramCollector(BaseCollector):
    """Collects from Telegram public channels via Telethon."""

    def __init__(self, keywords, hashtags, redis_stream=None, campaign_id="",
                 channels=None):
        super().__init__(Platform.TELEGRAM, keywords, hashtags, redis_stream, campaign_id)
        self.channels = channels or []

    def validate_credentials(self) -> bool:
        return bool(os.getenv("TELEGRAM_API_ID"))

    def collect(self):
        """Telegram collection requires async — see orchestrator for async runner."""
        self._collect_demo()

    async def collect_async(self):
        try:
            from telethon import TelegramClient
            api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
            api_hash = os.getenv("TELEGRAM_API_HASH", "")
            if not api_id or not api_hash:
                return

            async with TelegramClient("rie_session", api_id, api_hash) as client:
                for channel in self.channels:
                    try:
                        async for message in client.iter_messages(channel, limit=50):
                            if not message.text:
                                continue
                            if not any(kw.lower() in message.text.lower() for kw in self.keywords[:10]):
                                continue
                            mid = f"tg_{channel}_{message.id}"
                            if self._dedup_id(mid):
                                continue

                            dp = DataPoint(
                                source_platform=Platform.TELEGRAM,
                                source_id=mid,
                                content_type=ContentType.TEXT,
                                raw_text=message.text,
                                engagement=EngagementMetrics(views=message.views or 0),
                                temporal=TemporalInfo(created_at=message.date or datetime.utcnow()),
                            )
                            self.publish(dp)
                    except Exception as e:
                        logger.error(f"Telegram channel {channel} error: {e}")
        except ImportError:
            logger.warning("telethon not installed")

    def _collect_demo(self):
        demo = [
            "Forward from BJP Bengal: PM Modi will address a mega rally at Brigade. All karyakartas report by 12 PM.",
            "TMC Channel: BJP's rally will be a flop show. Bengal rejects outsider politics.",
        ]
        for i, text in enumerate(demo):
            dp = DataPoint(
                source_platform=Platform.TELEGRAM, source_id=f"demo_tg_{int(time.time())}_{i}",
                content_type=ContentType.TEXT, raw_text=text,
                temporal=TemporalInfo(created_at=datetime.utcnow()),
            )
            self.publish(dp)


# ─── COLLECTOR FACTORY ───────────────────────────────────────────────────

class CollectorFactory:
    """Create and manage all collectors for a campaign."""

    @staticmethod
    def create_all(keywords: list[str], hashtags: list[str],
                   redis_stream=None, campaign_id: str = "") -> dict:
        collectors = {
            "twitter": TwitterCollector(keywords, hashtags, redis_stream, campaign_id),
            "youtube": YouTubeCollector(keywords, hashtags, redis_stream, campaign_id),
            "reddit": RedditCollector(keywords, hashtags, redis_stream, campaign_id),
            "news": NewsCollector(keywords, hashtags, redis_stream, campaign_id),
            "google_trends": GoogleTrendsCollector(keywords, hashtags, redis_stream, campaign_id),
            "telegram": TelegramCollector(keywords, hashtags, redis_stream, campaign_id),
        }
        return collectors

    @staticmethod
    def run_all(collectors: dict):
        """Run one collection cycle for all collectors."""
        for name, collector in collectors.items():
            try:
                logger.info(f"Running collector: {name}")
                collector.collect()
            except Exception as e:
                logger.error(f"Collector {name} failed: {e}")
