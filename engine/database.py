"""
JanPulse AI — Database Layer
PostgreSQL for relational data, ClickHouse for time-series analytics, Redis for streaming.
"""

import os
import json
from datetime import datetime
from typing import Optional
from loguru import logger

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    psycopg2 = None

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None

try:
    import redis
except ImportError:
    redis = None


class DatabaseConfig:
    """Load DB config from environment."""
    def __init__(self):
        self.pg_host = os.getenv("POSTGRES_HOST", "localhost")
        self.pg_port = int(os.getenv("POSTGRES_PORT", 5432))
        self.pg_db = os.getenv("POSTGRES_DB", "rally_intelligence")
        self.pg_user = os.getenv("POSTGRES_USER", "rie_admin")
        self.pg_pass = os.getenv("POSTGRES_PASSWORD", "password")
        self.ch_host = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.ch_port = int(os.getenv("CLICKHOUSE_PORT", 8123))
        self.ch_db = os.getenv("CLICKHOUSE_DB", "rally_analytics")
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))


class PostgresDB:
    """PostgreSQL connection manager with context-manager support."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def is_connected(self) -> bool:
        return self._conn is not None

    def connect(self):
        if psycopg2 is None:
            logger.warning("psycopg2 not installed, using mock mode")
            return
        try:
            self._conn = psycopg2.connect(
                host=self.config.pg_host, port=self.config.pg_port,
                dbname=self.config.pg_db, user=self.config.pg_user,
                password=self.config.pg_pass
            )
            self._conn.autocommit = True
            logger.info(f"Connected to PostgreSQL at {self.config.pg_host}:{self.config.pg_port}")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            self._conn = None

    def execute(self, query: str, params=None):
        if not self._conn:
            logger.warning("No PG connection, skipping query")
            return []
        with self._conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []

    def insert_datapoint(self, dp: dict):
        query = """
            INSERT INTO data_points (
                doc_id, source_platform, source_id, source_url, content_type,
                raw_text, normalised_text, language_detected, language_script,
                author_id, author_name, follower_count, verified,
                likes, shares, comments, views,
                hashtags, mentions, geo_lat, geo_lon, geo_state, geo_district,
                created_at, collected_at, rally_phase,
                sentiment_label, sentiment_confidence,
                emotions_json, stance_json, entities_json, topics,
                sarcasm_flag, bot_suspicion_score, misinformation_flag,
                narrative_cluster_id, influence_score
            ) VALUES (
                %(doc_id)s, %(source_platform)s, %(source_id)s, %(source_url)s, %(content_type)s,
                %(raw_text)s, %(normalised_text)s, %(language_detected)s, %(language_script)s,
                %(author_id)s, %(author_name)s, %(follower_count)s, %(verified)s,
                %(likes)s, %(shares)s, %(comments)s, %(views)s,
                %(hashtags)s, %(mentions)s, %(geo_lat)s, %(geo_lon)s, %(geo_state)s, %(geo_district)s,
                %(created_at)s, %(collected_at)s, %(rally_phase)s,
                %(sentiment_label)s, %(sentiment_confidence)s,
                %(emotions_json)s, %(stance_json)s, %(entities_json)s, %(topics)s,
                %(sarcasm_flag)s, %(bot_suspicion_score)s, %(misinformation_flag)s,
                %(narrative_cluster_id)s, %(influence_score)s
            )
            ON CONFLICT (doc_id) DO NOTHING
        """
        self.execute(query, dp)

    def close(self):
        if self._conn:
            self._conn.close()


class RedisStream:
    """Redis Streams for real-time message passing."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._client = None

    def connect(self):
        if redis is None:
            logger.warning("redis not installed, using mock mode")
            return
        try:
            self._client = redis.Redis(
                host=self.config.redis_host, port=self.config.redis_port,
                decode_responses=True
            )
            self._client.ping()
            logger.info(f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._client = None

    def publish(self, stream: str, data: dict):
        if not self._client:
            return None
        serialised = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in data.items()}
        return self._client.xadd(stream, serialised, maxlen=100000)

    def consume(self, stream: str, group: str, consumer: str, count: int = 10, block: int = 5000):
        if not self._client:
            return []
        try:
            self._client.xgroup_create(stream, group, id="0", mkstream=True)
        except redis.exceptions.ResponseError:
            pass  # Group exists
        messages = self._client.xreadgroup(group, consumer, {stream: ">"}, count=count, block=block)
        return messages

    def ack(self, stream: str, group: str, *ids):
        if self._client:
            self._client.xack(stream, group, *ids)


# ─── SQL SCHEMA CREATION ─────────────────────────────────────────────────

POSTGRES_SCHEMA = """
-- Main data points table
CREATE TABLE IF NOT EXISTS data_points (
    doc_id VARCHAR(64) PRIMARY KEY,
    source_platform VARCHAR(32) NOT NULL,
    source_id VARCHAR(256),
    source_url TEXT,
    content_type VARCHAR(32) DEFAULT 'text',
    raw_text TEXT NOT NULL,
    normalised_text TEXT,
    language_detected VARCHAR(8) DEFAULT 'unknown',
    language_script VARCHAR(16) DEFAULT 'unknown',
    
    -- Author
    author_id VARCHAR(128),
    author_name VARCHAR(256),
    follower_count INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    
    -- Engagement
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    
    -- Metadata
    hashtags TEXT[],
    mentions TEXT[],
    geo_lat DOUBLE PRECISION,
    geo_lon DOUBLE PRECISION,
    geo_state VARCHAR(64),
    geo_district VARCHAR(64),
    
    -- Temporal
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    rally_phase VARCHAR(16),
    
    -- NLP Results
    sentiment_label VARCHAR(24),
    sentiment_confidence REAL,
    emotions_json JSONB,
    stance_json JSONB,
    entities_json JSONB,
    topics TEXT[],
    sarcasm_flag BOOLEAN DEFAULT FALSE,
    bot_suspicion_score REAL DEFAULT 0.0,
    misinformation_flag BOOLEAN DEFAULT FALSE,
    narrative_cluster_id VARCHAR(32),
    influence_score REAL DEFAULT 0.0,
    
    -- Indexing
    created_at_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_dp_platform ON data_points(source_platform);
CREATE INDEX IF NOT EXISTS idx_dp_phase ON data_points(rally_phase);
CREATE INDEX IF NOT EXISTS idx_dp_sentiment ON data_points(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_dp_created ON data_points(created_at);
CREATE INDEX IF NOT EXISTS idx_dp_date ON data_points(created_at_date);
CREATE INDEX IF NOT EXISTS idx_dp_lang ON data_points(language_detected);

-- KPI snapshots table
CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(64) NOT NULL,
    phase VARCHAR(16) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    window_start TIMESTAMP WITH TIME ZONE,
    window_end TIMESTAMP WITH TIME ZONE,
    kpi_data JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kpi_campaign ON kpi_snapshots(campaign_id, phase);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(64) PRIMARY KEY,
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    message TEXT,
    metric_name VARCHAR(64),
    metric_value REAL,
    threshold REAL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    campaign_id VARCHAR(64),
    acknowledged BOOLEAN DEFAULT FALSE
);

-- Influencer tracking
CREATE TABLE IF NOT EXISTS influencers (
    author_id VARCHAR(128) PRIMARY KEY,
    display_name VARCHAR(256),
    platform VARCHAR(32),
    follower_count INTEGER DEFAULT 0,
    influence_score REAL DEFAULT 0.0,
    stance VARCHAR(16),
    total_posts INTEGER DEFAULT 0,
    total_engagement INTEGER DEFAULT 0,
    avg_sentiment REAL DEFAULT 0.0,
    last_seen TIMESTAMP WITH TIME ZONE
);

-- Narrative clusters
CREATE TABLE IF NOT EXISTS narrative_clusters (
    cluster_id VARCHAR(32) PRIMARY KEY,
    phase VARCHAR(16),
    cluster_label VARCHAR(256),
    keywords TEXT[],
    sentiment_direction VARCHAR(16),
    strength REAL DEFAULT 0.0,
    doc_count INTEGER DEFAULT 0,
    representative_texts TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""


def setup_database():
    """Create all tables in PostgreSQL."""
    config = DatabaseConfig()
    with PostgresDB(config) as db:
        if db.is_connected:
            db.execute(POSTGRES_SCHEMA)
            logger.info("PostgreSQL schema created successfully")
        else:
            logger.error("Could not create schema — no database connection")


if __name__ == "__main__":
    setup_database()
