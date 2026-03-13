"""
JanPulse AI — Scoring Engine
Computes all 25+ KPIs from classified data. Outputs KPISnapshot objects.
"""

import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Optional
from loguru import logger

from engine.models import (
    DataPoint, KPISnapshot, SentimentShare, EmotionDistribution,
    RallyPhase, SentimentLabel, EmotionLabel, StanceLabel
)


class ScoringEngine:
    """
    Computes all KPIs for a given set of classified DataPoints.
    Can operate on any phase window or custom time window.
    """

    def __init__(self, campaign_id: str = "", campaign_config: dict = None):
        self.campaign_id = campaign_id
        self.config = campaign_config or {}
        self.primary_leader = self.config.get("primary_leader", "Narendra Modi")
        self.primary_party = self.config.get("primary_party", "BJP")

    def compute(self, datapoints: list[DataPoint], phase: RallyPhase,
                window_start: datetime = None, window_end: datetime = None,
                baseline: Optional[KPISnapshot] = None) -> KPISnapshot:
        """Compute full KPI snapshot from classified data points."""
        if not datapoints:
            return KPISnapshot(
                campaign_id=self.campaign_id, phase=phase,
                window_start=window_start or datetime.utcnow(),
                window_end=window_end or datetime.utcnow()
            )

        now = datetime.utcnow()
        ws = window_start or min(dp.temporal.created_at for dp in datapoints)
        we = window_end or max(dp.temporal.created_at for dp in datapoints)

        # Filter to only classified data
        classified = [dp for dp in datapoints if dp.nlp_results is not None]
        total = len(classified)

        if total == 0:
            return KPISnapshot(campaign_id=self.campaign_id, phase=phase,
                               window_start=ws, window_end=we, mention_volume=len(datapoints))

        kpi = KPISnapshot(
            campaign_id=self.campaign_id, phase=phase,
            timestamp=now, window_start=ws, window_end=we
        )

        # ── VOLUME METRICS ──
        kpi.mention_volume = len(datapoints)
        kpi.engagement_volume = sum(
            dp.engagement.likes + dp.engagement.shares + dp.engagement.comments + dp.engagement.views
            for dp in datapoints
        )
        total_reach = max(sum(dp.author.follower_count for dp in datapoints), 1)
        kpi.engagement_rate = (kpi.engagement_volume / total_reach) * 100 if total_reach > 0 else 0.0

        # ── SENTIMENT SHARE ──
        sentiments = Counter(dp.nlp_results.sentiment.label.value for dp in classified)
        kpi.sentiment_share = SentimentShare(
            positive=round(sentiments.get("positive", 0) / total * 100, 1),
            negative=round(sentiments.get("negative", 0) / total * 100, 1),
            neutral=round(sentiments.get("neutral", 0) / total * 100, 1),
            mixed=round(sentiments.get("mixed", 0) / total * 100, 1),
            total_docs=total
        )
        # Include sarcastic as negative in effective count
        sarc_pos = sentiments.get("sarcastic_positive", 0)
        if sarc_pos > 0:
            kpi.sentiment_share.negative += round(sarc_pos / total * 100, 1)

        # ── EMOTION DISTRIBUTION ──
        emotion_counts = defaultdict(float)
        emotion_n = 0
        for dp in classified:
            if dp.nlp_results.emotions:
                for e in dp.nlp_results.emotions:
                    emotion_counts[e.label.value] += e.score
                emotion_n += 1
        if emotion_n > 0:
            kpi.emotion_distribution = EmotionDistribution(**{
                k: round(v / emotion_n * 100, 1)
                for k, v in emotion_counts.items()
                if k in EmotionDistribution.model_fields
            })

        # ── LEADER FAVOURABILITY SCORE ──
        leader_docs = [dp for dp in classified if dp.nlp_results.stance.toward_leader != StanceLabel.UNDETERMINED]
        if leader_docs:
            support_count = sum(1 for dp in leader_docs if dp.nlp_results.stance.toward_leader == StanceLabel.SUPPORT)
            pos_sent_leader = sum(1 for dp in leader_docs if dp.nlp_results.sentiment.label == SentimentLabel.POSITIVE)
            trust_scores = [
                next((e.score for e in dp.nlp_results.emotions if e.label == EmotionLabel.TRUST), 0)
                for dp in leader_docs
            ]
            n = len(leader_docs)
            # Favourability: 40% positive sentiment + 30% leader support stance + 20% rally support + 10% trust
            rally_support = sum(
                1 for dp in leader_docs
                if dp.nlp_results.stance.toward_rally == StanceLabel.SUPPORT
            )
            kpi.leader_favourability_score = round(
                0.40 * (pos_sent_leader / n * 100) +
                0.30 * (support_count / n * 100) +
                0.20 * (rally_support / n * 100) +
                0.10 * (sum(trust_scores) / n * 100 if trust_scores else 0),
                1
            )

        # ── RALLY MOOD SCORE (simplified for non-live; full formula in live mode) ──
        pos_pct = kpi.sentiment_share.positive
        neg_pct = kpi.sentiment_share.negative
        excitement_score = emotion_counts.get("excitement", 0)
        hope_score = emotion_counts.get("hope", 0)
        anger_score = emotion_counts.get("anger", 0)

        mood_from_sentiment = ((pos_pct - neg_pct) + 100) / 2  # Normalise to 0-100
        mood_from_emotion = min(100, (excitement_score + hope_score - anger_score + 50))
        kpi.rally_mood_score = round(0.7 * mood_from_sentiment + 0.3 * mood_from_emotion, 1)
        kpi.rally_mood_score = max(0, min(100, kpi.rally_mood_score))

        # ── SHARE OF VOICE ──
        primary_mentions = sum(
            1 for dp in datapoints
            if self.primary_party.lower() in dp.raw_text.lower() or
               self.primary_leader.lower() in dp.raw_text.lower()
        )
        kpi.share_of_voice = round(primary_mentions / max(len(datapoints), 1) * 100, 1)

        # ── OPPOSITION COUNTER-NARRATIVE INTENSITY ──
        opposition_docs = [
            dp for dp in classified
            if dp.nlp_results.stance.toward_leader == StanceLabel.OPPOSE or
               dp.nlp_results.stance.toward_party == StanceLabel.OPPOSE
        ]
        opp_engagement = sum(
            dp.engagement.likes + dp.engagement.shares + dp.engagement.comments
            for dp in opposition_docs
        )
        kpi.opposition_counter_intensity = round(
            len(opposition_docs) / max(total, 1) * 100, 1
        )

        # ── BOT SUSPICION ──
        bot_flagged = sum(1 for dp in classified if dp.nlp_results.bot_suspicion_score > 0.6)
        kpi.bot_suspicion_score = round(bot_flagged / max(total, 1) * 100, 1)

        # ── POLARIZATION INDEX ──
        high_conf_polar = sum(
            1 for dp in classified
            if dp.nlp_results.sentiment.confidence > 0.85 and
               dp.nlp_results.sentiment.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE]
        )
        kpi.polarization_index = round(high_conf_polar / max(total, 1) * 100, 1)

        # ── MISINFORMATION FLAGS ──
        kpi.misinformation_flag_count = sum(
            1 for dp in classified if dp.nlp_results.misinformation_flag
        )

        # ── HASHTAG MOMENTUM ──
        hashtag_counter = Counter()
        for dp in datapoints:
            for ht in dp.metadata.hashtags:
                hashtag_counter[ht.lower()] += 1
        kpi.hashtag_momentum = dict(hashtag_counter.most_common(20))

        # ── TOP KEYWORDS ──
        word_counter = Counter()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
                      "for", "of", "and", "or", "but", "not", "this", "that", "it", "he",
                      "she", "they", "we", "you", "i", "me", "my", "rt", "amp", "ke", "ki",
                      "ka", "se", "ko", "hai", "hain", "nahi", "ya", "aur", "par"}
        for dp in datapoints:
            words = dp.raw_text.lower().split()
            for w in words:
                w = w.strip(".,!?#@\"'()[]{}:;")
                if len(w) > 2 and w not in stop_words:
                    word_counter[w] += 1
        kpi.top_keywords = [{"keyword": k, "count": v} for k, v in word_counter.most_common(30)]

        # ── TOP HASHTAGS ──
        kpi.top_hashtags = [{"hashtag": k, "count": v} for k, v in hashtag_counter.most_common(15)]

        # ── PLATFORM BREAKDOWN ──
        platform_counter = Counter(dp.source_platform.value for dp in datapoints)
        kpi.platform_breakdown = dict(platform_counter)

        # ── GEOGRAPHIC CONCENTRATION ──
        geo_counter = Counter()
        for dp in datapoints:
            if dp.metadata.geo.state:
                geo_counter[dp.metadata.geo.state] += 1
            if dp.metadata.geo.district:
                geo_counter[dp.metadata.geo.district] += 1
        kpi.geographic_concentration = dict(geo_counter.most_common(20))

        # ── COMMENT INTENSITY ──
        commented_posts = [dp for dp in datapoints if dp.engagement.comments > 0]
        if commented_posts:
            kpi.comment_intensity = round(
                sum(dp.engagement.comments for dp in commented_posts) / len(commented_posts), 1
            )

        # ── VIRALITY SCORE ──
        if datapoints:
            max_shares = max(dp.engagement.shares for dp in datapoints)
            avg_shares = sum(dp.engagement.shares for dp in datapoints) / len(datapoints)
            kpi.virality_score = round(min(100, (max_shares / max(avg_shares, 1)) * 10), 1)

        # ── SEARCH LIFT (if baseline provided) ──
        if baseline and baseline.mention_volume > 0:
            kpi.search_lift = round(
                (kpi.mention_volume - baseline.mention_volume) / baseline.mention_volume * 100, 1
            )

        # ── NARRATIVE SHIFT INDEX (simplified — full version uses BERTopic) ──
        if baseline and baseline.top_keywords:
            baseline_kws = set(k["keyword"] for k in baseline.top_keywords[:10])
            current_kws = set(k["keyword"] for k in kpi.top_keywords[:10])
            overlap = len(baseline_kws & current_kws)
            kpi.narrative_shift_index = round((1 - overlap / max(len(baseline_kws), 1)) * 100, 1)

        # ── TRUST/CONFIDENCE INDICATOR ──
        trust_docs = [
            dp for dp in classified
            if any(e.label == EmotionLabel.TRUST for e in dp.nlp_results.emotions)
        ]
        if trust_docs:
            avg_trust = sum(
                next(e.score for e in dp.nlp_results.emotions if e.label == EmotionLabel.TRUST)
                for dp in trust_docs
            ) / len(trust_docs)
            kpi.trust_confidence_indicator = round(avg_trust * 100, 1)

        # ── INFLUENCER DETECTION ──
        authors = defaultdict(lambda: {"engagement": 0, "posts": 0, "name": "", "followers": 0})
        for dp in datapoints:
            aid = dp.author.author_id
            authors[aid]["engagement"] += (dp.engagement.likes + dp.engagement.shares + dp.engagement.comments)
            authors[aid]["posts"] += 1
            authors[aid]["name"] = dp.author.display_name
            authors[aid]["followers"] = dp.author.follower_count

        sorted_influencers = sorted(authors.items(), key=lambda x: x[1]["engagement"], reverse=True)
        kpi.top_influencers = [
            {"author_id": aid, "name": data["name"], "engagement": data["engagement"],
             "posts": data["posts"], "followers": data["followers"]}
            for aid, data in sorted_influencers[:20]
        ]

        logger.info(f"KPI Snapshot computed: phase={phase.value}, mentions={kpi.mention_volume}, "
                     f"sentiment=+{kpi.sentiment_share.positive}/-{kpi.sentiment_share.negative}, "
                     f"mood={kpi.rally_mood_score}")

        return kpi

    def compute_rally_mood_live(self, datapoints: list[DataPoint],
                                 speech_applause_score: float = 50.0,
                                 crowd_energy_score: float = 50.0,
                                 media_framing_score: float = 50.0) -> float:
        """
        Compute live Rally Mood Score using the weighted composite formula.
        Called every 5 minutes during live rally.
        """
        if not datapoints:
            return 50.0

        classified = [dp for dp in datapoints if dp.nlp_results is not None]
        # Exclude bots
        clean = [dp for dp in classified if dp.nlp_results.bot_suspicion_score < 0.6]

        if not clean:
            return 50.0

        # Live comment polarity (25%)
        pos = sum(1 for dp in clean if dp.nlp_results.sentiment.label in
                  [SentimentLabel.POSITIVE])
        neg = sum(1 for dp in clean if dp.nlp_results.sentiment.label in
                  [SentimentLabel.NEGATIVE, SentimentLabel.SARCASTIC_POS])
        comment_polarity = ((pos - neg) / max(len(clean), 1) + 1) / 2 * 100

        # Viral quote emergence (20%) — proxy: share velocity
        total_shares = sum(dp.engagement.shares for dp in datapoints)
        avg_shares = total_shares / max(len(datapoints), 1)
        viral_score = min(100, avg_shares * 5)

        # Clip circulation speed (15%) — proxy: view velocity
        total_views = sum(dp.engagement.views for dp in datapoints)
        clip_score = min(100, (total_views / max(len(datapoints), 1)) / 10)

        # Composite
        mood = (
            0.25 * comment_polarity +
            0.20 * viral_score +
            0.15 * crowd_energy_score +
            0.15 * speech_applause_score +
            0.15 * clip_score +
            0.10 * media_framing_score
        )

        return round(max(0, min(100, mood)), 1)
