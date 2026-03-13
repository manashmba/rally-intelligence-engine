"""JanPulse AI — Demo data generators for dashboard callbacks."""
import random
from datetime import datetime, timedelta


def demo_dates(days=7):
    return [(datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%d %b") for i in range(days)]


def demo_advanced_sentiment():
    raw = {"Admiration": random.uniform(40, 58), "Neutral": random.uniform(25, 38),
           "Joy": random.uniform(3, 8), "Disgust": random.uniform(1.5, 5),
           "Sadness": random.uniform(0.2, 1.5), "Anger": random.uniform(0.5, 3),
           "Surprise": random.uniform(0.5, 2.5), "Fear": random.uniform(0.2, 1.2),
           "Sarcasm": random.uniform(0.5, 3), "Hope": random.uniform(2, 6)}
    total = sum(raw.values())
    return {k: round(v / total * 100, 1) for k, v in raw.items()}

ADV_COLORS = {"Admiration": "#C8963E", "Neutral": "#8E8E8E", "Joy": "#D4D455",
              "Disgust": "#2A9D8F", "Sadness": "#457B9D", "Anger": "#E63946",
              "Surprise": "#F4A261", "Fear": "#6D597A", "Sarcasm": "#B5838D", "Hope": "#52B788"}

ADV_EMOJIS = {"Admiration": "👍", "Neutral": "😐", "Joy": "😊", "Disgust": "🤢",
              "Anger": "😡", "Sadness": "😢", "Surprise": "😮", "Fear": "😨",
              "Sarcasm": "😏", "Hope": "🌟"}

PARTY_COLORS = {"BJP": "#FF6B00", "TMC": "#00BCD4", "LEFT": "#E53935",
                "Congress": "#1565C0", "Neutral": "#78909C", "Others": "#7E57C2"}
PARTY_BADGE = {"BJP": "warning", "TMC": "info", "LEFT": "danger",
               "Congress": "primary", "Neutral": "secondary", "Others": "light"}

PLAT_COLORS = {"twitter": "#1DA1F2", "facebook": "#4267B2", "youtube": "#FF0000",
               "news": "#F39C12", "reddit": "#FF4500", "instagram": "#E1306C"}


def demo_popular_mentions():
    return [
        {"text": "Massive turnout at Modi rally in Kolkata — the energy is unreal! 🇮🇳",
         "hashtags": ["#ModiInKolkata", "#BJP4Bengal"], "source": "twitter.com", "date": "2026-03-11 14:22", "engagement": 45200},
        {"text": "Historic crowd at Brigade Parade Ground. Bengal is ready for change!",
         "hashtags": ["#ModiMegaRally", "#BengalElection2026"], "source": "instagram.com", "date": "2026-03-11 13:45", "engagement": 38700},
        {"text": "PM Modi announces major infrastructure push for West Bengal during rally speech",
         "hashtags": ["#ModiInKolkata", "#DevForBengal"], "source": "ndtv.com", "date": "2026-03-11 15:10", "engagement": 32100},
        {"text": "Opposition calls the rally a 'show of money power' — TMC fires back",
         "hashtags": ["#KhelaHobe", "#BengalElection2026"], "source": "twitter.com", "date": "2026-03-11 16:05", "engagement": 28400},
        {"text": "Drone footage shows sea of supporters stretching across 3km at Kolkata rally",
         "hashtags": ["#ModiMegaRally"], "source": "youtube.com", "date": "2026-03-11 14:55", "engagement": 25800},
        {"text": "Key promises from PM Modi's Kolkata rally: MSP guarantee, job creation, free healthcare",
         "hashtags": ["#BJP4Bengal", "#NaMoBengal"], "source": "news18.com", "date": "2026-03-11 15:30", "engagement": 22300},
        {"text": "Local leaders join BJP ahead of rally — political realignment in Bengal?",
         "hashtags": ["#BengalPolitics", "#BJP4Bengal"], "source": "facebook.com", "date": "2026-03-11 12:15", "engagement": 18900},
        {"text": "Bengal students unite in support — youth voter turnout expected to be record high",
         "hashtags": ["#BengalElection2026", "#YouthVote"], "source": "reddit.com", "date": "2026-03-11 11:40", "engagement": 15600},
    ]


def demo_sm_mentions_table():
    return [
        ("yashanshu_singh", "X / Twitter", 73, "1.242%", 39900, "2m ago"),
        ("BJP4TheNilgiris", "X / Twitter", 3448, "1.176%", 37788, "5m ago"),
        ("ModiForIndia2026", "Instagram", 52000, "0.984%", 31600, "1m ago"),
        ("ai_daytrading", "X / Twitter", 1380, "0.784%", 25200, "8m ago"),
        ("BengalBJPVoice", "Facebook", 28000, "0.721%", 23200, "3m ago"),
        ("PoliticalBengal", "YouTube", 42000, "0.663%", 21300, "12m ago"),
        ("RockyBhai377", "X / Twitter", 540, "0.542%", 17400, "6m ago"),
        ("ajmalkhan_bjp", "X / Twitter", 198, "0.532%", 17100, "15m ago"),
        ("BengalRisingYouth", "Instagram", 15000, "0.498%", 16000, "4m ago"),
        ("RallyWatchIndia", "Reddit", 8200, "0.465%", 14900, "7m ago"),
        ("annamalai_k", "X / Twitter", 145000, "0.385%", 12400, "18m ago"),
        ("KolkataPulse", "X / Twitter", 8900, "0.265%", 8520, "9m ago"),
        ("NDTV_Bengali", "YouTube", 320000, "0.231%", 7430, "11m ago"),
        ("DebateIndia", "X / Twitter", 95000, "0.175%", 5630, "22m ago"),
    ]


def demo_trending_hashtags():
    return [
        ("arunprasad2578", "X / Twitter", 73, 43, "1m ago"),
        ("BJP4TheNilgiris", "X / Twitter", 3448, 25, "3m ago"),
        ("BengalBJP_FB", "Facebook", 18200, 22, "2m ago"),
        ("ayyanar_2023", "X / Twitter", 10, 16, "5m ago"),
        ("kumaravelbjp", "X / Twitter", 49, 13, "7m ago"),
        ("RallyReels_IG", "Instagram", 42000, 11, "4m ago"),
        ("SenthurStore", "X / Twitter", 939, 8, "10m ago"),
        ("PoliticsTodayYT", "YouTube", 128000, 8, "6m ago"),
        ("ai_daytrading", "X / Twitter", 1380, 7, "12m ago"),
        ("BengalReddit", "Reddit", 5400, 6, "8m ago"),
    ]


def demo_trending_topics():
    """Generate real-time trending topics across all platforms."""
    return [
        {"topic": "Modi Rally Kolkata", "volume": random.randint(8000, 15000),
         "trend": "🔺", "change": f"+{random.randint(120, 340)}%",
         "platforms": ["X/Twitter", "Facebook", "Instagram", "YouTube"],
         "sentiment": "Mostly Positive", "updated": "Just now"},
        {"topic": "Bengal Election 2026", "volume": random.randint(5000, 10000),
         "trend": "🔺", "change": f"+{random.randint(80, 200)}%",
         "platforms": ["X/Twitter", "Facebook", "News", "Reddit"],
         "sentiment": "Mixed", "updated": "1m ago"},
        {"topic": "Brigade Rally Crowd", "volume": random.randint(3000, 7000),
         "trend": "🔺", "change": f"+{random.randint(200, 500)}%",
         "platforms": ["X/Twitter", "Instagram", "YouTube"],
         "sentiment": "Positive", "updated": "2m ago"},
        {"topic": "Khela Hobe Response", "volume": random.randint(2500, 6000),
         "trend": "🔻", "change": f"-{random.randint(5, 20)}%",
         "platforms": ["X/Twitter", "Facebook"],
         "sentiment": "Negative (Anti-BJP)", "updated": "3m ago"},
        {"topic": "Bengal Development Plans", "volume": random.randint(1500, 4000),
         "trend": "🔺", "change": f"+{random.randint(40, 100)}%",
         "platforms": ["News", "X/Twitter", "YouTube"],
         "sentiment": "Positive", "updated": "5m ago"},
        {"topic": "Opposition Criticism", "volume": random.randint(1200, 3500),
         "trend": "➡️", "change": f"+{random.randint(2, 15)}%",
         "platforms": ["X/Twitter", "Facebook", "News"],
         "sentiment": "Negative", "updated": "4m ago"},
        {"topic": "Youth Voter Turnout", "volume": random.randint(800, 2500),
         "trend": "🔺", "change": f"+{random.randint(50, 150)}%",
         "platforms": ["Instagram", "Reddit", "X/Twitter"],
         "sentiment": "Neutral-Positive", "updated": "8m ago"},
        {"topic": "NRC Debate Bengal", "volume": random.randint(600, 2000),
         "trend": "🔻", "change": f"-{random.randint(10, 30)}%",
         "platforms": ["X/Twitter", "Facebook"],
         "sentiment": "Polarized", "updated": "12m ago"},
    ]


def demo_live_alerts():
    """Generate real-time live alerts across platforms."""
    alerts_pool = [
        {"level": "critical", "icon": "🔴", "msg": "Negative hashtag #ModiGoBack trending on X/Twitter — 2,400+ posts in last 30 min",
         "platform": "X / Twitter", "time": "Just now"},
        {"level": "warning", "icon": "🟠", "msg": "Bot spike detected on Facebook — 340% above baseline in rally-related groups",
         "platform": "Facebook", "time": "2m ago"},
        {"level": "warning", "icon": "🟠", "msg": "Coordinated posting pattern detected across 12 Instagram accounts sharing identical content",
         "platform": "Instagram", "time": "5m ago"},
        {"level": "info", "icon": "🔵", "msg": f"Rally hashtag #ModiInKolkata crossed {random.randint(5000, 8000):,} mentions — now trending nationally",
         "platform": "X / Twitter", "time": "3m ago"},
        {"level": "critical", "icon": "🔴", "msg": f"Negative sentiment spike on YouTube — {random.randint(15, 25)}% increase in critical video comments",
         "platform": "YouTube", "time": "8m ago"},
        {"level": "warning", "icon": "🟠", "msg": "Opposition Reddit thread gaining traction — r/IndianPolitics front page with anti-rally post",
         "platform": "Reddit", "time": "10m ago"},
        {"level": "info", "icon": "🔵", "msg": f"Positive engagement surge — Instagram Reels about rally crossed {random.randint(100, 500)}K views",
         "platform": "Instagram", "time": "4m ago"},
        {"level": "info", "icon": "🔵", "msg": "News outlet ABP Ananda running live coverage — sentiment tracker shows 62% positive reactions",
         "platform": "News / TV", "time": "6m ago"},
        {"level": "warning", "icon": "🟠", "msg": f"Polarization index rose to {random.randint(45, 60)}% — political divide deepening in online discourse",
         "platform": "Cross-Platform", "time": "15m ago"},
        {"level": "info", "icon": "🔵", "msg": f"Bengali-language positive content up {random.randint(20, 45)}% — regional support growing",
         "platform": "Cross-Platform", "time": "7m ago"},
    ]
    # Return 6-8 random alerts
    return random.sample(alerts_pool, min(random.randint(6, 8), len(alerts_pool)))


def demo_inf_stance():
    return [
        ("@BJPBengal", "BJP", "Strong Support", 0.94, "X / Twitter", "1m ago"),
        ("@NaMo_BJP", "BJP", "Strong Support", 0.91, "X / Twitter", "3m ago"),
        ("Suvendu Adhikari", "BJP", "Support", 0.88, "Facebook", "5m ago"),
        ("@AITCofficial", "TMC", "Strong Support", 0.95, "X / Twitter", "2m ago"),
        ("@MamataOfficial", "TMC", "Strong Support", 0.93, "X / Twitter", "4m ago"),
        ("TMC Youth Congress", "TMC", "Support", 0.87, "Instagram", "6m ago"),
        ("@CPIMBengal", "LEFT", "Strong Support", 0.92, "X / Twitter", "8m ago"),
        ("Student Federation", "LEFT", "Support", 0.85, "Facebook", "12m ago"),
        ("@ndtv", "Neutral", "Neutral Coverage", 0.78, "YouTube", "3m ago"),
        ("@ABPAnanda", "Neutral", "Neutral Coverage", 0.74, "X / Twitter", "7m ago"),
        ("India Today Bengali", "Neutral", "Slight BJP Lean", 0.65, "YouTube", "10m ago"),
        ("@DilipGhoshBJP", "BJP", "Support", 0.89, "X / Twitter", "5m ago"),
        ("@SaugataRoyMP", "TMC", "Support", 0.86, "X / Twitter", "9m ago"),
        ("Bengal Farmer Union", "LEFT", "Oppose BJP", 0.72, "Facebook", "15m ago"),
        ("@RepublicBangla", "BJP", "Slight Support", 0.68, "YouTube", "11m ago"),
        ("@TheWireBangla", "Others", "Critical of BJP", 0.71, "X / Twitter", "13m ago"),
        ("@ScrollBengal", "Others", "Critical of BJP", 0.67, "Reddit", "18m ago"),
        ("@Dev_Adhikari_", "BJP", "Support", 0.82, "Instagram", "6m ago"),
        ("@DidiKeBolo", "TMC", "Support", 0.80, "Facebook", "4m ago"),
        ("Bengal Against NRC", "TMC", "Oppose BJP", 0.76, "Reddit", "20m ago"),
    ]


def demo_ht_stance():
    return [
        ("#ModiInKolkata", "BJP", "Pro-BJP Rally", 4820, 0.96, "X / Twitter, Instagram", "1m ago"),
        ("#BJP4Bengal", "BJP", "Pro-BJP Campaign", 3540, 0.94, "X / Twitter, Facebook", "2m ago"),
        ("#ModiMegaRally", "BJP", "Pro-BJP Event", 2890, 0.92, "X / Twitter, YouTube", "3m ago"),
        ("#KhelaHobe", "TMC", "Pro-TMC Slogan", 5200, 0.97, "X / Twitter, Facebook, Instagram", "1m ago"),
        ("#DidiKeBolo", "TMC", "Pro-TMC Campaign", 2100, 0.91, "X / Twitter, Facebook", "5m ago"),
        ("#BengalWantsTMC", "TMC", "Pro-TMC", 1650, 0.88, "Facebook, Instagram", "8m ago"),
        ("#BengalElection2026", "Neutral", "General Election", 3200, 0.42, "All Platforms", "Just now"),
        ("#WestBengalPolls", "Neutral", "General Election", 1800, 0.38, "News, X / Twitter", "6m ago"),
        ("#NoNRC", "TMC", "Anti-BJP Policy", 1420, 0.84, "X / Twitter, Reddit", "10m ago"),
        ("#RedBengal", "LEFT", "Pro-LEFT", 890, 0.90, "X / Twitter, Facebook", "15m ago"),
        ("#CPIMRally", "LEFT", "Pro-LEFT Event", 620, 0.93, "X / Twitter", "12m ago"),
        ("#CongressForBengal", "Congress", "Pro-Congress", 450, 0.86, "Facebook, X / Twitter", "20m ago"),
        ("#BengalRising", "BJP", "Pro-BJP", 1950, 0.78, "Instagram, YouTube", "4m ago"),
        ("#JokhonDakBe", "TMC", "Pro-TMC Slogan", 980, 0.85, "X / Twitter, Facebook", "7m ago"),
        ("#BengalRejects", "Others", "Anti-Establishment", 720, 0.62, "Reddit, X / Twitter", "18m ago"),
    ]


# ─── Bot Activity Demo Data ──────────────────────────────────────────

BOT_INCLINATION_COLORS = {
    "Pro-BJP / PM Modi": "#FF6B00",
    "Anti-BJP (Opposition)": "#00BCD4",
    "Neutral / Undetermined": "#78909C",
}

BOT_SENTIMENT_COLORS = {
    "Positive (Pro-BJP/Modi)": "#FF6B00",
    "Negative (Anti-BJP)": "#00BCD4",
    "Negative (Anti-Opposition)": "#E53935",
    "Neutral / Spam": "#78909C",
}


BENGALI_HASHTAG_COLORS = {
    "Pro-BJP": "#FF6B00", "Pro-TMC": "#00BCD4", "Pro-LEFT": "#E53935",
    "Neutral": "#78909C", "Regional": "#52B788",
}


def demo_regional_bengali():
    """Generate demo data for Regional Bengali Pulse section."""
    bengali_mentions = random.randint(2200, 4800)
    bengali_positive = round(random.uniform(38, 58), 1)
    bengali_negative = round(random.uniform(18, 35), 1)
    bengali_reach = random.randint(120000, 450000)

    return {
        "total_mentions": bengali_mentions,
        "positive_pct": bengali_positive,
        "negative_pct": bengali_negative,
        "neutral_pct": round(100 - bengali_positive - bengali_negative, 1),
        "reach": bengali_reach,

        "hashtags": [
            {"tag": "#বাংলারমোদি", "en": "Modi of Bengal", "count": random.randint(800, 1800), "party": "Pro-BJP"},
            {"tag": "#খেলাহবে", "en": "Game On", "count": random.randint(1200, 2500), "party": "Pro-TMC"},
            {"tag": "#পরিবর্তন", "en": "Change", "count": random.randint(500, 1200), "party": "Neutral"},
            {"tag": "#বাংলারগর্ব", "en": "Pride of Bengal", "count": random.randint(400, 900), "party": "Regional"},
            {"tag": "#মোদিজিন্দাবাদ", "en": "Long Live Modi", "count": random.randint(600, 1500), "party": "Pro-BJP"},
            {"tag": "#মমতাদিদি", "en": "Mamata Didi", "count": random.randint(700, 1600), "party": "Pro-TMC"},
            {"tag": "#বাংলারউন্নয়ন", "en": "Bengal Development", "count": random.randint(300, 800), "party": "Neutral"},
            {"tag": "#জয়বাংলা", "en": "Victory Bengal", "count": random.randint(350, 900), "party": "Regional"},
            {"tag": "#বামফ্রন্ট", "en": "Left Front", "count": random.randint(200, 600), "party": "Pro-LEFT"},
            {"tag": "#নতুনবাংলা", "en": "New Bengal", "count": random.randint(250, 700), "party": "Neutral"},
        ],

        "influencers": [
            {"handle": "@BanglarKhabor", "name": "বাংলার খবর", "platform": "X / Twitter",
             "followers": random.randint(45000, 85000), "stance": "Neutral", "engagement": random.randint(3000, 8000)},
            {"handle": "@KolkataBarta", "name": "কলকাতা বার্তা", "platform": "Facebook",
             "followers": random.randint(60000, 120000), "stance": "Neutral", "engagement": random.randint(4000, 10000)},
            {"handle": "@BJP_Bangla", "name": "বিজেপি বাংলা", "platform": "X / Twitter",
             "followers": random.randint(80000, 180000), "stance": "Pro-BJP", "engagement": random.randint(5000, 12000)},
            {"handle": "@TMC_Bangla", "name": "তৃণমূল বাংলা", "platform": "X / Twitter",
             "followers": random.randint(70000, 160000), "stance": "Pro-TMC", "engagement": random.randint(4500, 11000)},
            {"handle": "@BanglaYuva", "name": "বাংলা যুব", "platform": "Instagram",
             "followers": random.randint(25000, 65000), "stance": "Neutral", "engagement": random.randint(2000, 6000)},
            {"handle": "@SonarBangla24", "name": "সোনার বাংলা ২৪", "platform": "YouTube",
             "followers": random.randint(100000, 250000), "stance": "Neutral", "engagement": random.randint(6000, 15000)},
            {"handle": "@DeshBangla", "name": "দেশ বাংলা", "platform": "Facebook",
             "followers": random.randint(35000, 75000), "stance": "Pro-LEFT", "engagement": random.randint(2500, 7000)},
            {"handle": "@BengaliVoice_", "name": "বাঙালি কণ্ঠ", "platform": "X / Twitter",
             "followers": random.randint(15000, 45000), "stance": "Regional", "engagement": random.randint(1500, 5000)},
        ],

        "sentiment_by_topic": {
            "Rally/সভা": {"pos": round(random.uniform(40, 60), 1), "neg": round(random.uniform(15, 30), 1)},
            "Economy/অর্থনীতি": {"pos": round(random.uniform(25, 45), 1), "neg": round(random.uniform(25, 40), 1)},
            "Jobs/চাকরি": {"pos": round(random.uniform(20, 40), 1), "neg": round(random.uniform(30, 50), 1)},
            "Identity/পরিচয়": {"pos": round(random.uniform(35, 55), 1), "neg": round(random.uniform(20, 35), 1)},
            "Development/উন্নয়ন": {"pos": round(random.uniform(30, 50), 1), "neg": round(random.uniform(20, 35), 1)},
        },

        "regional_vs_national": {
            "regional_positive": bengali_positive,
            "national_positive": round(random.uniform(35, 55), 1),
            "regional_negative": bengali_negative,
            "national_negative": round(random.uniform(20, 35), 1),
        },

        "key_insight": f"Bengali-language discourse accounts for ~{random.randint(28, 42)}% of total rally mentions. "
                       f"{'Pro-BJP Bengali hashtags are trending higher than opposition' if bengali_positive > 45 else 'Opposition Bengali hashtags are gaining traction'}. "
                       f"Regional sentiment is {'more positive' if bengali_positive > 45 else 'slightly more critical'} than national average.",
    }


def demo_bot_activity():
    """Generate demo bot activity analysis data."""
    total_accounts = random.randint(18000, 25000)
    bot_accounts = random.randint(1400, 2200)
    bot_pct = round(bot_accounts / total_accounts * 100, 1)

    pro_bjp_modi = round(random.uniform(35, 48), 1)
    pro_opposition_negative = round(random.uniform(28, 42), 1)
    neutral_bots = round(100 - pro_bjp_modi - pro_opposition_negative, 1)

    return {
        "total_accounts_analyzed": total_accounts,
        "bot_accounts_detected": bot_accounts,
        "bot_percentage": bot_pct,
        "human_accounts": total_accounts - bot_accounts,
        "confidence_score": round(random.uniform(0.82, 0.96), 2),
        "political_inclination": {
            "Pro-BJP / PM Modi": pro_bjp_modi,
            "Anti-BJP (Opposition)": pro_opposition_negative,
            "Neutral / Undetermined": neutral_bots,
        },
        "bot_sentiment": {
            "Positive (Pro-BJP/Modi)": round(random.uniform(30, 45), 1),
            "Negative (Anti-BJP)": round(random.uniform(25, 38), 1),
            "Negative (Anti-Opposition)": round(random.uniform(8, 18), 1),
            "Neutral / Spam": round(random.uniform(10, 20), 1),
        },
        "bot_platforms": {
            "Twitter/X": round(random.uniform(45, 58), 1),
            "Facebook": round(random.uniform(18, 28), 1),
            "Instagram": round(random.uniform(8, 15), 1),
            "YouTube": round(random.uniform(4, 10), 1),
            "Others": round(random.uniform(2, 6), 1),
        },
        "top_bot_hashtags": [
            {"hashtag": "ModiInKolkata", "bot_pct": round(random.uniform(12, 22), 1), "inclination": "Pro-BJP"},
            {"hashtag": "BJP4Bengal", "bot_pct": round(random.uniform(10, 18), 1), "inclination": "Pro-BJP"},
            {"hashtag": "KhelaHobe", "bot_pct": round(random.uniform(15, 25), 1), "inclination": "Pro-TMC"},
            {"hashtag": "ModiGoBack", "bot_pct": round(random.uniform(18, 30), 1), "inclination": "Anti-BJP"},
            {"hashtag": "BengalRejects", "bot_pct": round(random.uniform(20, 35), 1), "inclination": "Anti-BJP"},
            {"hashtag": "ModiMegaRally", "bot_pct": round(random.uniform(8, 15), 1), "inclination": "Pro-BJP"},
        ],
        "bot_activity_timeline": [
            round(random.uniform(2, 6), 1),
            round(random.uniform(3, 7), 1),
            round(random.uniform(4, 8), 1),
            round(random.uniform(5, 10), 1),
            round(random.uniform(8, 15), 1),
            round(random.uniform(12, 22), 1),
            round(random.uniform(10, 18), 1),
        ],
        "key_findings": [
            f"~{bot_pct}% of total accounts show bot-like behavior patterns",
            f"Pro-BJP/Modi bots are {pro_bjp_modi:.0f}% of all bot activity — mostly amplifying rally hashtags",
            f"Anti-BJP opposition bots account for {pro_opposition_negative:.0f}% — spreading negative narratives",
            f"Bot activity spiked {round(random.uniform(180, 320))}% during rally hours vs. pre-rally baseline",
            "Coordinated bot clusters detected on Twitter/X and Facebook targeting rally-related discourse",
        ],
    }
