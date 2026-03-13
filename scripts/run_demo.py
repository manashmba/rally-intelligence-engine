#!/usr/bin/env python3
"""
JanPulse AI — Quick Start Demo
Runs the full pipeline with synthetic data. No API keys required.

Usage: python scripts/run_demo.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO",
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")

def main():
    print("=" * 70)
    print("  RALLY INTELLIGENCE ENGINE — DEMO MODE")
    print("  No API keys required. Using synthetic data.")
    print("=" * 70)
    print()

    # Import engine
    from engine.orchestrator import RallyIntelligenceEngine

    # Initialise (skip heavy model loading for demo)
    engine = RallyIntelligenceEngine()
    engine.initialise(load_models=False)

    # Run demo
    kpi = engine._run_demo()

    if kpi:
        print()
        print("=" * 70)
        print("  RESULTS SUMMARY")
        print("=" * 70)
        print(f"  Rally Mood Score:       {kpi.rally_mood_score}/100")
        print(f"  Total Mentions:         {kpi.mention_volume}")
        print(f"  Positive Sentiment:     {kpi.sentiment_share.positive}%")
        print(f"  Negative Sentiment:     {kpi.sentiment_share.negative}%")
        print(f"  Neutral Sentiment:      {kpi.sentiment_share.neutral}%")
        print(f"  Leader Favourability:   {kpi.leader_favourability_score}/100")
        print(f"  Share of Voice:         {kpi.share_of_voice}%")
        print(f"  Bot Suspicion:          {kpi.bot_suspicion_score}%")
        print(f"  Polarization Index:     {kpi.polarization_index}")
        print(f"  Platforms Monitored:    {len(kpi.platform_breakdown)}")
        print(f"  Top Hashtags:           {[h['hashtag'] for h in kpi.top_hashtags[:5]]}")
        print()
        print(f"  Report generated at:    reports/")
        print("=" * 70)
        print()
        print("  To run with real data, configure .env with API keys and run:")
        print("  python -m engine.orchestrator start --mode pre-rally")
        print()
        print("  To launch the dashboard:")
        print("  python engine/dashboard/server.py --port 8050")
        print()
        print("  To deploy with Docker:")
        print("  docker-compose up -d")
        print("=" * 70)

if __name__ == "__main__":
    main()
