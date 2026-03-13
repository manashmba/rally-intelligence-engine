# JanPulse AI

**AI-Powered Public Mood & Rally Sentiment Analysis Platform**

Built for Indian State Election Campaign Intelligence — by Mindgen Pvt Ltd

---

## Overview

The JanPulse AI monitors, analyses, and reports on public mood surrounding political rallies in Indian state elections. It ingests data from 14+ digital platforms, processes content in 5+ Indian languages (Bengali, Hindi, English, Hinglish, Romanised Bengali), computes 25+ KPIs, and generates automated rally intelligence reports.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RALLY INTELLIGENCE ENGINE                       │
├─────────────┬──────────────┬──────────────┬────────────────────────┤
│  L1: DATA   │  L2: STREAM  │  L3: STORAGE │  L4: NLP PIPELINE     │
│  INGESTION  │  PROCESSING  │              │                        │
│  ─────────  │  ──────────  │  ──────────  │  ──────────────────    │
│  Twitter    │  Redis       │  PostgreSQL  │  Language Detection    │
│  YouTube    │  Streams     │  ClickHouse  │  Sentiment (MuRIL)    │
│  Facebook   │  Dedup       │  MinIO       │  Emotion (XLM-R)      │
│  Reddit     │  Routing     │  (S3)        │  Stance (LLM)         │
│  Telegram   │              │              │  NER (IndicNER)       │
│  News/RSS   │              │              │  Topic (BERTopic)     │
│  G.Trends   │              │              │  Sarcasm Detection    │
│  Speech     │              │              │  Bot Scoring          │
├─────────────┴──────────────┴──────────────┴────────────────────────┤
│  L5: LLM ORCHESTRATION  │  L6: SCORING   │  L7: DASHBOARD/ALERTS │
│  ──────────────────────  │  ───────────   │  ─────────────────    │
│  Claude API              │  Rally Mood    │  Grafana (live)       │
│  GPT-4o API              │  Score         │  Superset (analytics) │
│  LangChain               │  All 25+ KPIs │  Slack/Email/SMS      │
│  Narrative Summaries     │  Phase-based   │  React Dashboard      │
├──────────────────────────┴────────────────┴────────────────────────┤
│  L8: REPORT GENERATION                                             │
│  ─────────────────────                                             │
│  python-docx + Matplotlib + Jinja2 → 50-page DOCX/PDF             │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose
- NVIDIA GPU (for NLP models) — optional for demo mode
- API Keys (see `.env.example`)

### 2. Installation

```bash
# Clone and setup
cd rally-intelligence-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Run database setup
python scripts/setup_database.py

# Launch with Docker Compose
docker-compose up -d
```

### 3. Configure a Rally Campaign

```bash
python -m engine.cli create-campaign \
  --config config/campaigns/wb_kolkata_rally_2026.json
```

### 4. Start Monitoring

```bash
# Start all collectors
python -m engine.orchestrator start --mode pre-rally

# Start NLP pipeline
python -m engine.nlp.pipeline start

# Launch dashboard
python -m engine.dashboard.server start --port 8050
```

### 5. Generate Report

```bash
python -m engine.reports.generator generate \
  --campaign wb_2026_kolkata_rally_001 \
  --phase post_24h \
  --output reports/rally_report_24h.docx
```

## Project Structure

```
rally-intelligence-engine/
├── config/                  # Configuration files
│   ├── campaigns/           # Rally campaign definitions
│   ├── taxonomy/            # Classification taxonomies
│   ├── keywords/            # Keyword corpora (multilingual)
│   └── alerts/              # Alert threshold configs
├── engine/                  # Core engine modules
│   ├── ingestion/           # Data collectors per platform
│   ├── nlp/                 # NLP pipeline (5-layer stack)
│   ├── scoring/             # KPI computation engine
│   ├── reports/             # Automated report generator
│   ├── alerts/              # Alert engine
│   ├── dashboard/           # Web dashboard
│   ├── models.py            # Data models & schemas
│   ├── database.py          # Database connections
│   ├── orchestrator.py      # Pipeline orchestrator
│   └── cli.py               # Command-line interface
├── templates/               # Report templates
├── scripts/                 # Setup & utility scripts
├── tests/                   # Test suite
├── docker-compose.yml       # Container orchestration
├── Dockerfile               # Main application container
├── requirements.txt         # Python dependencies
└── .env.example             # Environment template
```

## License

Proprietary — Mindgen Pvt Ltd. All rights reserved.
