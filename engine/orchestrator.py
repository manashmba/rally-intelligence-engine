"""
JanPulse AI — Main Orchestrator
Coordinates data collection, NLP processing, scoring, alerting, and reporting.
Supports three modes: pre-rally, live-rally, post-rally.
"""

import os
import sys
import json
import time
import signal
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from loguru import logger

from engine.models import (
    DataPoint, KPISnapshot, RallyPhase, CampaignConfig,
    Platform, ContentType, AuthorInfo, EngagementMetrics,
    ContentMetadata, TemporalInfo, GeoInfo
)
from engine.database import PostgresDB, RedisStream, DatabaseConfig
from engine.ingestion.collectors import CollectorFactory
from engine.nlp.pipeline import NLPPipeline
from engine.scoring.engine import ScoringEngine
from engine.alerts.engine import AlertEngine
from engine.reports.generator import ReportGenerator


class RallyIntelligenceEngine:
    """
    Main orchestrator for JanPulse AI.
    Manages the full lifecycle: collection → processing → scoring → alerting → reporting.
    """

    def __init__(self, config_path: str = None):
        self.running = False
        self.config = self._load_config(config_path)
        self.campaign_id = self.config.get("campaign_id", "default")
        self.keywords, self.hashtags = self._load_keywords()

        # Core components
        self.db = PostgresDB()
        self.redis = RedisStream()
        self.collectors = {}
        self.nlp_pipeline = None
        self.scoring_engine = ScoringEngine(self.campaign_id, self.config)
        self.alert_engine = AlertEngine(campaign_id=self.campaign_id)
        self.report_generator = ReportGenerator(self.config)

        # State
        self.data_buffer: list[DataPoint] = []
        self.classified_buffer: list[DataPoint] = []
        self.kpi_history: list[KPISnapshot] = []
        self.current_phase: RallyPhase = RallyPhase.PRE_7D

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _load_config(self, path: str = None) -> dict:
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        # Try default
        default = "config/campaigns/wb_kolkata_rally_2026.json"
        if os.path.exists(default):
            with open(default, encoding="utf-8") as f:
                return json.load(f)
        logger.warning("No campaign config found, using defaults")
        return {"campaign_id": "default", "primary_leader": "Narendra Modi", "primary_party": "BJP"}

    def _load_keywords(self) -> tuple[list[str], list[str]]:
        kw_path = self.config.get("keyword_corpus_path", "config/keywords/wb_rally_001.json")
        if os.path.exists(kw_path):
            with open(kw_path, encoding="utf-8") as f:
                corpus = json.load(f)
            keywords = []
            hashtags = []
            for cat in corpus.get("categories", {}).values():
                if isinstance(cat, dict):
                    for subcat in cat.values():
                        if isinstance(subcat, dict) and "variants" in subcat:
                            for lang, terms in subcat["variants"].items():
                                keywords.extend(terms)
                        elif isinstance(subcat, list):
                            hashtags.extend(subcat)
            # Deduplicate
            keywords = list(set(keywords))[:100]
            hashtags = list(set(hashtags))[:30]
            logger.info(f"Loaded {len(keywords)} keywords and {len(hashtags)} hashtags")
            return keywords, hashtags
        logger.warning("No keyword corpus found")
        return ["Modi", "BJP", "rally", "Kolkata", "TMC", "Mamata"], ["#ModiInKolkata"]

    def initialise(self, load_models: bool = True):
        """Initialise all components."""
        logger.info("=" * 60)
        logger.info("JANPULSE AI — INITIALISING")
        logger.info(f"Campaign: {self.campaign_id}")
        logger.info("=" * 60)

        # Database
        self.db.connect()
        self.redis.connect()

        # Collectors
        self.collectors = CollectorFactory.create_all(
            self.keywords, self.hashtags, self.redis, self.campaign_id
        )
        logger.info(f"Initialised {len(self.collectors)} collectors")

        # NLP Pipeline
        corpus_path = self.config.get("keyword_corpus_path", "")
        corpus = {}
        if os.path.exists(corpus_path):
            with open(corpus_path, encoding="utf-8") as f:
                corpus = json.load(f)

        self.nlp_pipeline = NLPPipeline(
            keyword_corpus=corpus,
            use_gpu=os.getenv("NLP_DEVICE", "cpu") == "cuda",
            use_llm=bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")),
            campaign_config=self.config
        )

        if load_models:
            logger.info("Loading NLP models (this may take a few minutes)...")
            self.nlp_pipeline.load_models()

        logger.info("Engine initialised successfully")

    def determine_phase(self) -> RallyPhase:
        """Determine current rally phase based on time."""
        now = datetime.utcnow()
        rally_start_str = self.config.get("rally_start_time", "")
        rally_end_str = self.config.get("rally_end_time", "")

        try:
            from dateutil import parser
            rally_start = parser.parse(rally_start_str).replace(tzinfo=None) if rally_start_str else now + timedelta(days=7)
            rally_end = parser.parse(rally_end_str).replace(tzinfo=None) if rally_end_str else rally_start + timedelta(hours=3)
        except Exception:
            rally_start = now + timedelta(days=7)
            rally_end = rally_start + timedelta(hours=3)

        delta = rally_start - now
        if now > rally_end + timedelta(hours=72):
            return RallyPhase.POST_72H
        elif now > rally_end + timedelta(hours=48):
            return RallyPhase.POST_48H
        elif now > rally_end + timedelta(hours=24):
            return RallyPhase.POST_24H
        elif now > rally_end + timedelta(hours=6):
            return RallyPhase.POST_6H
        elif now > rally_end + timedelta(hours=2):
            return RallyPhase.POST_2H
        elif now >= rally_start:
            return RallyPhase.LIVE
        elif delta <= timedelta(hours=6):
            return RallyPhase.PRE_6H
        elif delta <= timedelta(hours=24):
            return RallyPhase.PRE_24H
        elif delta <= timedelta(days=3):
            return RallyPhase.PRE_3D
        else:
            return RallyPhase.PRE_7D

    def run_collection_cycle(self):
        """Run one data collection cycle across all platforms."""
        logger.info(f"[Collection Cycle] Phase: {self.current_phase.value}")
        CollectorFactory.run_all(self.collectors)

        total = sum(c.collected_count for c in self.collectors.values())
        logger.info(f"[Collection Cycle] Total collected this session: {total}")

    def run_nlp_cycle(self, batch_size: int = 100):
        """Process collected data through NLP pipeline."""
        # In production, this reads from Redis stream
        # For demo, process data_buffer directly
        if not self.data_buffer:
            logger.debug("No data in buffer for NLP processing")
            return

        batch = self.data_buffer[:batch_size]
        self.data_buffer = self.data_buffer[batch_size:]

        classified = self.nlp_pipeline.process_batch(batch)

        for dp in classified:
            dp.temporal.rally_phase = self.current_phase
            self.classified_buffer.append(dp)

        logger.info(f"[NLP Cycle] Processed {len(classified)} documents. Buffer: {len(self.classified_buffer)}")

    def run_scoring_cycle(self):
        """Compute KPIs from classified data."""
        if not self.classified_buffer:
            logger.debug("No classified data for scoring")
            return None

        baseline = self.kpi_history[-1] if self.kpi_history else None
        kpi = self.scoring_engine.compute(
            self.classified_buffer, self.current_phase,
            baseline=baseline
        )
        self.kpi_history.append(kpi)

        # Store in database
        try:
            self.db.execute(
                "INSERT INTO kpi_snapshots (campaign_id, phase, kpi_data) VALUES (%s, %s, %s)",
                (self.campaign_id, self.current_phase.value, json.dumps(kpi.model_dump(), default=str))
            )
        except Exception as e:
            logger.debug(f"KPI storage error (non-critical): {e}")

        return kpi

    def run_alert_cycle(self, kpi: KPISnapshot = None):
        """Evaluate alert rules against latest KPI."""
        if not kpi:
            return
        alerts = self.alert_engine.evaluate(kpi)
        if alerts:
            self.alert_engine.dispatch(alerts)
            logger.warning(f"[Alert Cycle] {len(alerts)} alerts fired")

    def generate_report(self, phase: str = None, output_dir: str = "reports"):
        """Generate intelligence report for specified phase."""
        os.makedirs(output_dir, exist_ok=True)
        if not self.kpi_history:
            logger.warning("No KPI data available for report generation")
            return

        kpi = self.kpi_history[-1]
        baseline = self.kpi_history[0] if len(self.kpi_history) > 1 else None

        # Generate narrative summary via LLM
        narrative = None
        if self.nlp_pipeline and self.nlp_pipeline.llm_engine:
            sample_docs = [
                {"text": dp.raw_text[:200], "sentiment": dp.nlp_results.sentiment.label.value,
                 "platform": dp.source_platform.value}
                for dp in self.classified_buffer[:50] if dp.nlp_results
            ]
            if sample_docs:
                narrative = self.nlp_pipeline.llm_engine.summarise_narratives(
                    sample_docs, self.current_phase.value
                )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(output_dir, f"rally_report_{kpi.phase.value}_{timestamp}.docx")

        self.report_generator.generate(kpi, narrative, baseline, output_path)
        logger.info(f"Report generated: {output_path}")
        return output_path

    def start(self, mode: str = "pre-rally", interval_seconds: int = 300):
        """
        Start the engine in the specified mode.
        Modes: pre-rally, live, post-rally, demo
        """
        self.running = True
        self.current_phase = self.determine_phase()

        logger.info("=" * 60)
        logger.info(f"ENGINE STARTED — Mode: {mode}, Phase: {self.current_phase.value}")
        logger.info(f"Collection interval: {interval_seconds}s")
        logger.info("=" * 60)

        if mode == "demo":
            self._run_demo()
            return

        # Schedule collection cycles
        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                self.current_phase = self.determine_phase()
                logger.info(f"\n--- Cycle {cycle_count} | Phase: {self.current_phase.value} ---")

                # 1. Collect data
                self.run_collection_cycle()

                # 2. Move collected data to buffer (in production, via Redis)
                for collector in self.collectors.values():
                    # Demo mode: collectors publish to buffer directly
                    pass

                # 3. NLP processing
                self.run_nlp_cycle()

                # 4. Scoring
                kpi = self.run_scoring_cycle()

                # 5. Alerting
                self.run_alert_cycle(kpi)

                # 6. Report (every 6 hours or on demand)
                if cycle_count % (6 * 3600 // interval_seconds) == 0:
                    self.generate_report()

                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                time.sleep(30)

        logger.info("Engine stopped")

    def _run_demo(self):
        """Run a complete demo cycle with synthetic data."""
        logger.info("=" * 60)
        logger.info("RUNNING DEMO MODE")
        logger.info("=" * 60)

        # 1. Collect demo data
        logger.info("\n[Step 1] Collecting demo data...")
        self.run_collection_cycle()

        # Gather demo data from collectors into buffer
        import random
        demo_texts = [
            ("Modi rally in Kolkata looks like it will be massive! BJP is going all out #ModiInKolkata", "twitter"),
            ("Why is PM Modi wasting time in Bengal? Focus on national issues #KhelaHobe", "twitter"),
            ("Brigade Parade Ground packed! Historic rally incoming!", "twitter"),
            ("Didi will show BJP their place. Bengal doesn't need outsiders", "facebook"),
            ("कोलकाता में मोदी जी की रैली जबरदस्त होने वाली है! #ModiMegaRally", "twitter"),
            ("বিজেপি বাংলায় কিছুই করতে পারবে না। খেলা হবে!", "facebook"),
            ("Empty promises again. Same old jumla sarkar.", "twitter"),
            ("Modi's rally will change Bengal forever. Development is coming!", "youtube"),
            ("Good speech but where are the jobs he promised?", "youtube"),
            ("Waah kya vikas ho raha hai, sab kuch barbaad", "twitter"),
            ("PM Modi addresses lakhs at Brigade. Thunderous response!", "news"),
            ("TMC claims BJP rally used paid crowd. BJP denies.", "news"),
            ("Modi promises 10 lakh jobs for Bengal youth #BJP4Bengal", "twitter"),
            ("Rally was well-attended but speech lacked substance on real issues", "reddit"),
            ("As a Bengali, I think Modi genuinely cares about Bengal development", "reddit"),
            ("Another election gimmick. Nothing changes after the rally ends.", "twitter"),
            ("Massive crowd at Kolkata rally shows BJP's growing support in Bengal", "news"),
            ("Opposition running scared. Khela shesh! #ModiInKolkata", "twitter"),
            ("Modi ji ne kamaal kar diya. Bengal badlega ab! 🙏", "instagram"),
            ("Modiji er rally te onek lok esechilo. Bhalo laglo.", "sharechat"),
        ]

        from engine.models import (
            Platform, ContentType, AuthorInfo, EngagementMetrics,
            ContentMetadata, TemporalInfo
        )

        platform_map = {
            "twitter": Platform.TWITTER, "facebook": Platform.FACEBOOK,
            "youtube": Platform.YOUTUBE, "reddit": Platform.REDDIT,
            "news": Platform.NEWS, "instagram": Platform.INSTAGRAM,
            "sharechat": Platform.SHARECHAT
        }

        for i, (text, plat) in enumerate(demo_texts):
            dp = DataPoint(
                source_platform=platform_map.get(plat, Platform.TWITTER),
                source_id=f"demo_{i}_{int(time.time())}",
                content_type=ContentType.TEXT,
                raw_text=text,
                author=AuthorInfo(
                    author_id=f"user_{i}",
                    display_name=f"DemoUser{i}",
                    follower_count=random.randint(100, 100000),
                    account_age_days=random.randint(30, 2000),
                ),
                engagement=EngagementMetrics(
                    likes=random.randint(5, 2000),
                    shares=random.randint(0, 500),
                    comments=random.randint(0, 100),
                    views=random.randint(100, 50000),
                ),
                metadata=ContentMetadata(
                    hashtags=random.sample(
                        ["ModiInKolkata", "KhelaHobe", "BJP4Bengal", "BengalElection2026", "ModiMegaRally"],
                        k=random.randint(0, 3)
                    ),
                    geo=GeoInfo(
                        state="West Bengal", district=random.choice(["Kolkata", "Howrah", "North 24 Parganas", "Hooghly"])
                    )
                ),
                temporal=TemporalInfo(
                    created_at=datetime.utcnow() - timedelta(minutes=random.randint(0, 120))
                ),
            )
            self.data_buffer.append(dp)

        logger.info(f"[Step 1 Complete] {len(self.data_buffer)} documents in buffer")

        # 2. NLP Processing
        logger.info("\n[Step 2] Running NLP Pipeline...")
        self.run_nlp_cycle(batch_size=100)
        logger.info(f"[Step 2 Complete] {len(self.classified_buffer)} classified documents")

        # 3. Scoring
        logger.info("\n[Step 3] Computing KPIs...")
        kpi = self.run_scoring_cycle()
        if kpi:
            logger.info(f"[Step 3 Complete] Rally Mood Score: {kpi.rally_mood_score}")
            logger.info(f"  Sentiment: +{kpi.sentiment_share.positive}% / -{kpi.sentiment_share.negative}%")
            logger.info(f"  Mentions: {kpi.mention_volume}")
            logger.info(f"  Leader Favourability: {kpi.leader_favourability_score}")
            logger.info(f"  Top Hashtags: {kpi.top_hashtags[:5]}")

        # 4. Alerts
        logger.info("\n[Step 4] Checking Alerts...")
        self.run_alert_cycle(kpi)

        # 5. Report
        logger.info("\n[Step 5] Generating Report...")
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        report_path = self.generate_report(output_dir=report_dir)
        if report_path:
            logger.info(f"[Step 5 Complete] Report: {report_path}")

        logger.info("\n" + "=" * 60)
        logger.info("DEMO COMPLETE")
        logger.info("=" * 60)

        return kpi

    def _shutdown(self, signum, frame):
        logger.info("Shutdown signal received")
        self.running = False


# ─── CLI ENTRY POINT ─────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="JanPulse AI — India's Public Mood Analysis Engine")
    parser.add_argument("command", choices=["start", "demo", "report", "status"],
                       help="Command to execute")
    parser.add_argument("--config", default=None, help="Campaign config path")
    parser.add_argument("--mode", default="pre-rally",
                       choices=["pre-rally", "live", "post-rally", "demo"])
    parser.add_argument("--interval", type=int, default=300, help="Collection interval (seconds)")
    parser.add_argument("--output", default="reports", help="Report output directory")
    parser.add_argument("--no-models", action="store_true", help="Skip loading NLP models")

    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"),
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    logger.add("logs/rie_{time}.log", rotation="100 MB", level="DEBUG")

    engine = RallyIntelligenceEngine(config_path=args.config)
    engine.initialise(load_models=not args.no_models)

    if args.command == "demo" or args.mode == "demo":
        engine._run_demo()
    elif args.command == "start":
        engine.start(mode=args.mode, interval_seconds=args.interval)
    elif args.command == "report":
        engine.generate_report(output_dir=args.output)
    elif args.command == "status":
        logger.info(f"Campaign: {engine.campaign_id}")
        logger.info(f"Phase: {engine.determine_phase().value}")
        logger.info(f"Collectors: {list(engine.collectors.keys())}")


if __name__ == "__main__":
    main()
