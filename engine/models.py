"""
JanPulse AI — Core Data Models
Pydantic models defining all data schemas used across the system.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ─── ENUMS / TAXONOMY ────────────────────────────────────────────────────

class Platform(str, Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    TELEGRAM = "telegram"
    SHARECHAT = "sharechat"
    MOJ_JOSH = "moj_josh"
    NEWS = "news"
    GOOGLE_TRENDS = "google_trends"
    LIVESTREAM_CHAT = "livestream_chat"
    SPEECH_TRANSCRIPT = "speech_transcript"
    BLOG_FORUM = "blog_forum"


class ContentType(str, Enum):
    TEXT = "text"
    COMMENT = "comment"
    REPLY = "reply"
    LIVE_CHAT = "live_chat"
    HEADLINE = "headline"
    TRANSCRIPT_SEGMENT = "transcript_segment"
    SEARCH_TREND = "search_trend"
    VIDEO_POST = "video_post"
    RETWEET = "retweet"
    QUOTE_TWEET = "quote_tweet"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    SARCASTIC_POS = "sarcastic_positive"
    SARCASTIC_NEG = "sarcastic_negative"


class EmotionLabel(str, Enum):
    HOPE = "hope"
    ANGER = "anger"
    PRIDE = "pride"
    FEAR = "fear"
    TRUST = "trust"
    EXCITEMENT = "excitement"
    FRUSTRATION = "frustration"
    DISGUST = "disgust"
    SARCASM = "sarcasm"
    JOY = "joy"
    SADNESS = "sadness"


class StanceLabel(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    UNDETERMINED = "undetermined"


class RallyPhase(str, Enum):
    PRE_7D = "pre_7d"
    PRE_3D = "pre_3d"
    PRE_24H = "pre_24h"
    PRE_6H = "pre_6h"
    LIVE = "live"
    POST_2H = "post_2h"
    POST_6H = "post_6h"
    POST_24H = "post_24h"
    POST_48H = "post_48h"
    POST_72H = "post_72h"


class LanguageCode(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    BENGALI = "bn"
    HINGLISH = "hi-en"
    BANGLISH = "bn-en"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    INFO = "info"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── SUB-MODELS ──────────────────────────────────────────────────────────

class AuthorInfo(BaseModel):
    author_id: str
    display_name: str = ""
    follower_count: int = 0
    verified: bool = False
    account_age_days: int = 0
    bot_score: Optional[float] = None


class EngagementMetrics(BaseModel):
    likes: int = 0
    shares: int = 0
    comments: int = 0
    views: int = 0
    reactions: dict = Field(default_factory=lambda: {
        "like": 0, "love": 0, "haha": 0, "wow": 0, "sad": 0, "angry": 0
    })


class GeoInfo(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    place_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


class ContentMetadata(BaseModel):
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    media_type: str = "none"
    geo: GeoInfo = Field(default_factory=GeoInfo)
    in_reply_to: Optional[str] = None
    parent_id: Optional[str] = None
    conversation_thread_id: Optional[str] = None


class TemporalInfo(BaseModel):
    created_at: datetime
    collected_at: datetime = Field(default_factory=lambda: datetime.now(tz=None))
    rally_phase: Optional[RallyPhase] = None


class EmotionScore(BaseModel):
    label: EmotionLabel
    score: float = Field(ge=0.0, le=1.0)


class EntityDetection(BaseModel):
    text: str
    entity_type: str  # PERSON, ORG, LOC, EVENT, ISSUE
    normalised: str = ""


class SentimentResult(BaseModel):
    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    method: str = "transformer"  # transformer | llm | lexicon | rules


class StanceResult(BaseModel):
    toward_leader: StanceLabel = StanceLabel.UNDETERMINED
    toward_party: StanceLabel = StanceLabel.UNDETERMINED
    toward_rally: StanceLabel = StanceLabel.UNDETERMINED
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class NLPResults(BaseModel):
    sentiment: SentimentResult
    emotions: list[EmotionScore] = Field(default_factory=list)
    stance: StanceResult = Field(default_factory=StanceResult)
    entities: list[EntityDetection] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    sarcasm_flag: bool = False
    sarcasm_confidence: float = 0.0
    bot_suspicion_score: float = 0.0
    misinformation_flag: bool = False
    narrative_cluster_id: Optional[str] = None
    influence_score: float = 0.0


# ─── PRIMARY DATA MODEL ─────────────────────────────────────────────────

class DataPoint(BaseModel):
    """Universal data point schema — every piece of content in the system."""
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_platform: Platform
    source_id: str = ""
    source_url: str = ""
    content_type: ContentType = ContentType.TEXT
    raw_text: str
    normalised_text: str = ""
    language_detected: LanguageCode = LanguageCode.UNKNOWN
    language_script: str = "unknown"  # latin, devanagari, bengali, mixed
    author: AuthorInfo = Field(default_factory=lambda: AuthorInfo(author_id="unknown"))
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)
    metadata: ContentMetadata = Field(default_factory=ContentMetadata)
    temporal: TemporalInfo = Field(default_factory=lambda: TemporalInfo(created_at=datetime.utcnow()))
    nlp_results: Optional[NLPResults] = None

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


# ─── KPI MODELS ──────────────────────────────────────────────────────────

class SentimentShare(BaseModel):
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0
    mixed: float = 0.0
    total_docs: int = 0


class EmotionDistribution(BaseModel):
    hope: float = 0.0
    anger: float = 0.0
    pride: float = 0.0
    fear: float = 0.0
    trust: float = 0.0
    excitement: float = 0.0
    frustration: float = 0.0
    disgust: float = 0.0
    sarcasm: float = 0.0
    joy: float = 0.0
    sadness: float = 0.0


class KPISnapshot(BaseModel):
    """Complete KPI snapshot for a given phase and time window."""
    campaign_id: str
    phase: RallyPhase
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    window_start: datetime
    window_end: datetime

    # Volume
    mention_volume: int = 0
    engagement_volume: int = 0
    engagement_rate: float = 0.0

    # Sentiment
    sentiment_share: SentimentShare = Field(default_factory=SentimentShare)
    emotion_distribution: EmotionDistribution = Field(default_factory=EmotionDistribution)

    # Composite scores
    leader_favourability_score: float = 0.0
    rally_resonance_score: float = 0.0
    rally_mood_score: float = 50.0  # 0-100, 50 = neutral
    speech_pickup_score: float = 0.0

    # Competitive
    share_of_voice: float = 0.0
    opposition_counter_intensity: float = 0.0

    # Quality & Risk
    virality_score: float = 0.0
    bot_suspicion_score: float = 0.0
    polarization_index: float = 0.0
    misinformation_flag_count: int = 0

    # Trends
    hashtag_momentum: dict = Field(default_factory=dict)
    search_lift: float = 0.0
    video_view_velocity: float = 0.0
    comment_intensity: float = 0.0
    meme_spread_index: float = 0.0
    narrative_shift_index: float = 0.0
    trust_confidence_indicator: float = 0.0
    media_pickup_score: float = 0.0

    # Geographic
    geographic_concentration: dict = Field(default_factory=dict)

    # Platform breakdown
    platform_breakdown: dict = Field(default_factory=dict)

    # Top items
    top_keywords: list[dict] = Field(default_factory=list)
    top_hashtags: list[dict] = Field(default_factory=list)
    top_influencers: list[dict] = Field(default_factory=list)
    top_influencers_positive: list[dict] = Field(default_factory=list)
    top_influencers_negative: list[dict] = Field(default_factory=list)
    top_narratives: list[dict] = Field(default_factory=list)


# ─── CAMPAIGN CONFIG MODEL ───────────────────────────────────────────────

class RallyLocation(BaseModel):
    venue: str
    city: str
    state: str
    geo: GeoInfo


class MonitoringWindow(BaseModel):
    pre_start: datetime
    post_end: datetime


class TeamNotify(BaseModel):
    slack_channel: str = ""
    email_list: list[str] = Field(default_factory=list)
    whatsapp_group_id: str = ""


class CampaignConfig(BaseModel):
    """Rally monitoring campaign configuration."""
    campaign_id: str
    rally_name: str
    rally_date: str
    rally_start_time: datetime
    rally_end_time: datetime
    rally_location: RallyLocation
    primary_leader: str
    primary_party: str
    opposition_entities: list[str] = Field(default_factory=list)
    monitoring_window: MonitoringWindow
    languages: list[str] = Field(default_factory=lambda: ["en", "hi", "bn"])
    keyword_corpus_path: str = ""
    taxonomy_path: str = ""
    alert_thresholds_path: str = ""
    report_template_path: str = ""
    team_notify: TeamNotify = Field(default_factory=TeamNotify)


# ─── ALERT MODEL ─────────────────────────────────────────────────────────

class Alert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str
    severity: AlertSeverity
    message: str
    metric_name: str
    metric_value: float
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    campaign_id: str = ""
    acknowledged: bool = False
