#!/usr/bin/env python3
"""
JanPulse AI — Database Setup Script
Creates all required tables in PostgreSQL.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from engine.database import setup_database

if __name__ == "__main__":
    print("Setting up JanPulse AI database...")
    setup_database()
    print("Done!")
