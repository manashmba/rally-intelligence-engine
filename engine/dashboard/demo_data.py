"""JanPulse AI — Demo data generators for dashboard callbacks.

All timestamps use IST (UTC+5:30) and are dynamically computed from
the current wall-clock time so the dashboard always feels *live*.

Data values use a time-based seed that changes every 60 seconds, giving
smooth drift instead of wild jumps on each 10-second refresh.
"""
import random
import math
from datetime import datetime, timedelta, timezone

# ─── IST timezone ────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))


def _now_ist():
    return datetime.now(IST)


def _seed_for_minute():
    """Return a seed that changes every 60 s — gives stable-ish data."""
    t = _now_ist()
    return int(t.timestamp()) // 60


def _seeded_random():
    """Return a Random instance seeded to the current minute."""
    return random.Random(_seed_for_minute())


def _relative_time(minutes_ago: int) -> str:
    """'Just now', '2m ago', '1h ago', etc. from minutes_ago offset."""
    if minutes_ago <= 0:
        return "Just now"
    if minutes_ago < 60:
        return f"{minutes_ago}m ago"
    h = minutes_ago // 60
    return f"{h}h ago"


def _ist_stamp(minutes_ago: int) -> str:
    """Absolute IST timestamp string like '14:22 IST'."""
    t = _now_ist() - timedelta(minutes=minutes_ago)
    return t.strftime("%H:%M IST")


def _ist_datetime(minutes_ago: int) -> str:
    """Full IST datetime string like '2026-03-13 14:22'."""
    t = _now_ist() - timedelta(minutes=minutes_ago)
    return t.strftime("%Y-%m-%d %H:%M")


# ─── Public helpers ─────────────────────────────────────────────────

def demo_dates(days=7):
    now = _now_ist()
    return [(now - timedelta(days=days - 1 - i)).strftime("%d %b") for i in range(days)]


def demo_advanced_sentiment():
    r = _seeded_random()
    raw = {"Admiration": r.uniform(40, 58), "Neutral": r.uniform(25, 38),
           "Joy": r.uniform(3, 8), "Disgust": r.uniform(1.5, 5),
           "Sadness": r.uniform(0.2, 1.5), "Anger": r.uniform(0.5, 3),
           "Surprise": r.uniform(0.5, 2.5), "Fear": r.uniform(0.2, 1.2),
           "Sarcasm": r.uniform(0.5, 3), "Hope": r.uniform(2, 6)}
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
    """Top-8 popular mentions with live IST timestamps."""
    now = _now_ist()
    return [
        {"text": "Massive turnout at Modi rally in Kolkata — the energy is unreal! 🇮🇳",
         "hashtags": ["#ModiInKolkata", "#BJP4Bengal"], "source": "twitter.com",
         "date": _ist_datetime(38), "engagement": 45200},
        {"text": "Historic crowd at Brigade Parade Ground. Bengal is ready for change!",
         "hashtags": ["#ModiMegaRally", "#BengalElection2026"], "source": "instagram.com",
         "date": _ist_datetime(55), "engagement": 38700},
        {"text": "PM Modi announces major infrastructure push for West Bengal during rally speech",
         "hashtags": ["#ModiInKolkata", "#DevForBengal"], "source": "ndtv.com",
         "date": _ist_datetime(22), "engagement": 32100},
        {"text": "Opposition calls the rally a 'show of money power' — TMC fires back",
         "hashtags": ["#KhelaHobe", "#BengalElection2026"], "source": "twitter.com",
         "date": _ist_datetime(15), "engagement": 28400},
        {"text": "Drone footage shows sea of supporters stretching across 3km at Kolkata rally",
         "hashtags": ["#ModiMegaRally"], "source": "youtube.com",
         "date": _ist_datetime(30), "engagement": 25800},
        {"text": "Key promises from PM Modi's Kolkata rally: MSP guarantee, job creation, free healthcare",
         "hashtags": ["#BJP4Bengal", "#NaMoBengal"], "source": "news18.com",
         "date": _ist_datetime(10), "engagement": 22300},
        {"text": "Local leaders join BJP ahead of rally — political realignment in Bengal?",
         "hashtags": ["#BengalPolitics", "#BJP4Bengal"], "source": "facebook.com",
         "date": _ist_datetime(90), "engagement": 18900},
        {"text": "Bengal students unite in support — youth voter turnout expected to be record high",
         "hashtags": ["#BengalElection2026", "#YouthVote"], "source": "reddit.com",
         "date": _ist_datetime(120), "engagement": 15600},
    ]


def demo_sm_mentions_table():
    """Top social-media mention profiles with live relative timestamps."""
    r = _seeded_random()
    base = [
        ("yashanshu_singh", "X / Twitter", 73, "1.242%", 39900),
        ("BJP4TheNilgiris", "X / Twitter", 3448, "1.176%", 37788),
        ("ModiForIndia2026", "Instagram", 52000, "0.984%", 31600),
        ("ai_daytrading", "X / Twitter", 1380, "0.784%", 25200),
        ("BengalBJPVoice", "Facebook", 28000, "0.721%", 23200),
        ("PoliticalBengal", "YouTube", 42000, "0.663%", 21300),
        ("RockyBhai377", "X / Twitter", 540, "0.542%", 17400),
        ("ajmalkhan_bjp", "X / Twitter", 198, "0.532%", 17100),
        ("BengalRisingYouth", "Instagram", 15000, "0.498%", 16000),
        ("RallyWatchIndia", "Reddit", 8200, "0.465%", 14900),
        ("annamalai_k", "X / Twitter", 145000, "0.385%", 12400),
        ("KolkataPulse", "X / Twitter", 8900, "0.265%", 8520),
        ("NDTV_Bengali", "YouTube", 320000, "0.231%", 7430),
        ("DebateIndia", "X / Twitter", 95000, "0.175%", 5630),
    ]
    offsets = [r.randint(1, 3), r.randint(3, 6), r.randint(1, 2), r.randint(6, 10),
               r.randint(2, 5), r.randint(10, 15), r.randint(4, 8), r.randint(12, 18),
               r.randint(3, 6), r.randint(5, 9), r.randint(15, 22), r.randint(7, 12),
               r.randint(9, 14), r.randint(18, 28)]
    return [(*row, _relative_time(off)) for row, off in zip(base, offsets)]


def demo_trending_hashtags():
    r = _seeded_random()
    base = [
        ("arunprasad2578", "X / Twitter", 73, 43),
        ("BJP4TheNilgiris", "X / Twitter", 3448, 25),
        ("BengalBJP_FB", "Facebook", 18200, 22),
        ("ayyanar_2023", "X / Twitter", 10, 16),
        ("kumaravelbjp", "X / Twitter", 49, 13),
        ("RallyReels_IG", "Instagram", 42000, 11),
        ("SenthurStore", "X / Twitter", 939, 8),
        ("PoliticsTodayYT", "YouTube", 128000, 8),
        ("ai_daytrading", "X / Twitter", 1380, 7),
        ("BengalReddit", "Reddit", 5400, 6),
    ]
    offsets = [r.randint(0, 2), r.randint(2, 5), r.randint(1, 4), r.randint(4, 7),
               r.randint(5, 9), r.randint(3, 6), r.randint(8, 13), r.randint(5, 8),
               r.randint(10, 15), r.randint(6, 10)]
    return [(*row, _relative_time(off)) for row, off in zip(base, offsets)]


def demo_trending_topics():
    """Generate real-time trending topics with live IST timestamps."""
    r = _seeded_random()
    return [
        {"topic": "Modi Rally Kolkata", "volume": r.randint(8000, 15000),
         "trend": "🔺", "change": f"+{r.randint(120, 340)}%",
         "platforms": ["X/Twitter", "Facebook", "Instagram", "YouTube"],
         "sentiment": "Mostly Positive", "updated": _relative_time(r.randint(0, 1))},
        {"topic": "Bengal Election 2026", "volume": r.randint(5000, 10000),
         "trend": "🔺", "change": f"+{r.randint(80, 200)}%",
         "platforms": ["X/Twitter", "Facebook", "News", "Reddit"],
         "sentiment": "Mixed", "updated": _relative_time(r.randint(1, 3))},
        {"topic": "Brigade Rally Crowd", "volume": r.randint(3000, 7000),
         "trend": "🔺", "change": f"+{r.randint(200, 500)}%",
         "platforms": ["X/Twitter", "Instagram", "YouTube"],
         "sentiment": "Positive", "updated": _relative_time(r.randint(2, 5))},
        {"topic": "Khela Hobe Response", "volume": r.randint(2500, 6000),
         "trend": "🔻", "change": f"-{r.randint(5, 20)}%",
         "platforms": ["X/Twitter", "Facebook"],
         "sentiment": "Negative (Anti-BJP)", "updated": _relative_time(r.randint(3, 6))},
        {"topic": "Bengal Development Plans", "volume": r.randint(1500, 4000),
         "trend": "🔺", "change": f"+{r.randint(40, 100)}%",
         "platforms": ["News", "X/Twitter", "YouTube"],
         "sentiment": "Positive", "updated": _relative_time(r.randint(4, 8))},
        {"topic": "Opposition Criticism", "volume": r.randint(1200, 3500),
         "trend": "➡️", "change": f"+{r.randint(2, 15)}%",
         "platforms": ["X/Twitter", "Facebook", "News"],
         "sentiment": "Negative", "updated": _relative_time(r.randint(3, 7))},
        {"topic": "Youth Voter Turnout", "volume": r.randint(800, 2500),
         "trend": "🔺", "change": f"+{r.randint(50, 150)}%",
         "platforms": ["Instagram", "Reddit", "X/Twitter"],
         "sentiment": "Neutral-Positive", "updated": _relative_time(r.randint(6, 12))},
        {"topic": "NRC Debate Bengal", "volume": r.randint(600, 2000),
         "trend": "🔻", "change": f"-{r.randint(10, 30)}%",
         "platforms": ["X/Twitter", "Facebook"],
         "sentiment": "Polarized", "updated": _relative_time(r.randint(10, 18))},
    ]


def demo_live_alerts():
    """Generate real-time live alerts with IST timestamps."""
    r = _seeded_random()
    alerts_pool = [
        {"level": "critical", "icon": "🔴",
         "msg": "Negative hashtag #ModiGoBack trending on X/Twitter — 2,400+ posts in last 30 min",
         "platform": "X / Twitter", "time": _relative_time(r.randint(0, 2))},
        {"level": "warning", "icon": "🟠",
         "msg": "Bot spike detected on Facebook — 340% above baseline in rally-related groups",
         "platform": "Facebook", "time": _relative_time(r.randint(1, 4))},
        {"level": "warning", "icon": "🟠",
         "msg": "Coordinated posting pattern detected across 12 Instagram accounts sharing identical content",
         "platform": "Instagram", "time": _relative_time(r.randint(3, 7))},
        {"level": "info", "icon": "🔵",
         "msg": f"Rally hashtag #ModiInKolkata crossed {r.randint(5000, 8000):,} mentions — now trending nationally",
         "platform": "X / Twitter", "time": _relative_time(r.randint(2, 5))},
        {"level": "critical", "icon": "🔴",
         "msg": f"Negative sentiment spike on YouTube — {r.randint(15, 25)}% increase in critical video comments",
         "platform": "YouTube", "time": _relative_time(r.randint(6, 12))},
        {"level": "warning", "icon": "🟠",
         "msg": "Opposition Reddit thread gaining traction — r/IndianPolitics front page with anti-rally post",
         "platform": "Reddit", "time": _relative_time(r.randint(8, 14))},
        {"level": "info", "icon": "🔵",
         "msg": f"Positive engagement surge — Instagram Reels about rally crossed {r.randint(100, 500)}K views",
         "platform": "Instagram", "time": _relative_time(r.randint(3, 6))},
        {"level": "info", "icon": "🔵",
         "msg": "News outlet ABP Ananda running live coverage — sentiment tracker shows 62% positive reactions",
         "platform": "News / TV", "time": _relative_time(r.randint(5, 9))},
        {"level": "warning", "icon": "🟠",
         "msg": f"Polarization index rose to {r.randint(45, 60)}% — political divide deepening in online discourse",
         "platform": "Cross-Platform", "time": _relative_time(r.randint(12, 20))},
        {"level": "info", "icon": "🔵",
         "msg": f"Bengali-language positive content up {r.randint(20, 45)}% — regional support growing",
         "platform": "Cross-Platform", "time": _relative_time(r.randint(5, 10))},
    ]
    return r.sample(alerts_pool, min(r.randint(6, 8), len(alerts_pool)))


def demo_inf_stance():
    r = _seeded_random()
    return [
        ("@BJPBengal", "BJP", "Strong Support", 0.94, "X / Twitter", _relative_time(r.randint(0, 3))),
        ("@NaMo_BJP", "BJP", "Strong Support", 0.91, "X / Twitter", _relative_time(r.randint(2, 5))),
        ("Suvendu Adhikari", "BJP", "Support", 0.88, "Facebook", _relative_time(r.randint(4, 8))),
        ("@AITCofficial", "TMC", "Strong Support", 0.95, "X / Twitter", _relative_time(r.randint(1, 4))),
        ("@MamataOfficial", "TMC", "Strong Support", 0.93, "X / Twitter", _relative_time(r.randint(3, 6))),
        ("TMC Youth Congress", "TMC", "Support", 0.87, "Instagram", _relative_time(r.randint(5, 9))),
        ("@CPIMBengal", "LEFT", "Strong Support", 0.92, "X / Twitter", _relative_time(r.randint(6, 12))),
        ("Student Federation", "LEFT", "Support", 0.85, "Facebook", _relative_time(r.randint(10, 16))),
        ("@ndtv", "Neutral", "Neutral Coverage", 0.78, "YouTube", _relative_time(r.randint(2, 5))),
        ("@ABPAnanda", "Neutral", "Neutral Coverage", 0.74, "X / Twitter", _relative_time(r.randint(5, 10))),
        ("India Today Bengali", "Neutral", "Slight BJP Lean", 0.65, "YouTube", _relative_time(r.randint(8, 14))),
        ("@DilipGhoshBJP", "BJP", "Support", 0.89, "X / Twitter", _relative_time(r.randint(4, 7))),
        ("@SaugataRoyMP", "TMC", "Support", 0.86, "X / Twitter", _relative_time(r.randint(7, 12))),
        ("Bengal Farmer Union", "LEFT", "Oppose BJP", 0.72, "Facebook", _relative_time(r.randint(12, 20))),
        ("@RepublicBangla", "BJP", "Slight Support", 0.68, "YouTube", _relative_time(r.randint(9, 15))),
        ("@TheWireBangla", "Others", "Critical of BJP", 0.71, "X / Twitter", _relative_time(r.randint(10, 18))),
        ("@ScrollBengal", "Others", "Critical of BJP", 0.67, "Reddit", _relative_time(r.randint(15, 24))),
        ("@Dev_Adhikari_", "BJP", "Support", 0.82, "Instagram", _relative_time(r.randint(5, 9))),
        ("@DidiKeBolo", "TMC", "Support", 0.80, "Facebook", _relative_time(r.randint(3, 6))),
        ("Bengal Against NRC", "TMC", "Oppose BJP", 0.76, "Reddit", _relative_time(r.randint(16, 26))),
    ]


def demo_ht_stance():
    r = _seeded_random()
    return [
        ("#ModiInKolkata", "BJP", "Pro-BJP Rally", 4820, 0.96, "X / Twitter, Instagram", _relative_time(r.randint(0, 2))),
        ("#BJP4Bengal", "BJP", "Pro-BJP Campaign", 3540, 0.94, "X / Twitter, Facebook", _relative_time(r.randint(1, 4))),
        ("#ModiMegaRally", "BJP", "Pro-BJP Event", 2890, 0.92, "X / Twitter, YouTube", _relative_time(r.randint(2, 5))),
        ("#KhelaHobe", "TMC", "Pro-TMC Slogan", 5200, 0.97, "X / Twitter, Facebook, Instagram", _relative_time(r.randint(0, 3))),
        ("#DidiKeBolo", "TMC", "Pro-TMC Campaign", 2100, 0.91, "X / Twitter, Facebook", _relative_time(r.randint(4, 8))),
        ("#BengalWantsTMC", "TMC", "Pro-TMC", 1650, 0.88, "Facebook, Instagram", _relative_time(r.randint(6, 12))),
        ("#BengalElection2026", "Neutral", "General Election", 3200, 0.42, "All Platforms", _relative_time(r.randint(0, 1))),
        ("#WestBengalPolls", "Neutral", "General Election", 1800, 0.38, "News, X / Twitter", _relative_time(r.randint(5, 9))),
        ("#NoNRC", "TMC", "Anti-BJP Policy", 1420, 0.84, "X / Twitter, Reddit", _relative_time(r.randint(8, 14))),
        ("#RedBengal", "LEFT", "Pro-LEFT", 890, 0.90, "X / Twitter, Facebook", _relative_time(r.randint(12, 20))),
        ("#CPIMRally", "LEFT", "Pro-LEFT Event", 620, 0.93, "X / Twitter", _relative_time(r.randint(10, 16))),
        ("#CongressForBengal", "Congress", "Pro-Congress", 450, 0.86, "Facebook, X / Twitter", _relative_time(r.randint(16, 26))),
        ("#BengalRising", "BJP", "Pro-BJP", 1950, 0.78, "Instagram, YouTube", _relative_time(r.randint(3, 7))),
        ("#JokhonDakBe", "TMC", "Pro-TMC Slogan", 980, 0.85, "X / Twitter, Facebook", _relative_time(r.randint(5, 10))),
        ("#BengalRejects", "Others", "Anti-Establishment", 720, 0.62, "Reddit, X / Twitter", _relative_time(r.randint(14, 24))),
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
    r = _seeded_random()
    bengali_mentions = r.randint(2200, 4800)
    bengali_positive = round(r.uniform(38, 58), 1)
    bengali_negative = round(r.uniform(18, 35), 1)
    bengali_reach = r.randint(120000, 450000)

    return {
        "total_mentions": bengali_mentions,
        "positive_pct": bengali_positive,
        "negative_pct": bengali_negative,
        "neutral_pct": round(100 - bengali_positive - bengali_negative, 1),
        "reach": bengali_reach,

        "hashtags": [
            {"tag": "#বাংলারমোদি", "en": "Modi of Bengal", "count": r.randint(800, 1800), "party": "Pro-BJP"},
            {"tag": "#খেলাহবে", "en": "Game On", "count": r.randint(1200, 2500), "party": "Pro-TMC"},
            {"tag": "#পরিবর্তন", "en": "Change", "count": r.randint(500, 1200), "party": "Neutral"},
            {"tag": "#বাংলারগর্ব", "en": "Pride of Bengal", "count": r.randint(400, 900), "party": "Regional"},
            {"tag": "#মোদিজিন্দাবাদ", "en": "Long Live Modi", "count": r.randint(600, 1500), "party": "Pro-BJP"},
            {"tag": "#মমতাদিদি", "en": "Mamata Didi", "count": r.randint(700, 1600), "party": "Pro-TMC"},
            {"tag": "#বাংলারউন্নয়ন", "en": "Bengal Development", "count": r.randint(300, 800), "party": "Neutral"},
            {"tag": "#জয়বাংলা", "en": "Victory Bengal", "count": r.randint(350, 900), "party": "Regional"},
            {"tag": "#বামফ্রন্ট", "en": "Left Front", "count": r.randint(200, 600), "party": "Pro-LEFT"},
            {"tag": "#নতুনবাংলা", "en": "New Bengal", "count": r.randint(250, 700), "party": "Neutral"},
        ],

        "influencers": [
            {"handle": "@BanglarKhabor", "name": "বাংলার খবর", "platform": "X / Twitter",
             "followers": r.randint(45000, 85000), "stance": "Neutral", "engagement": r.randint(3000, 8000)},
            {"handle": "@KolkataBarta", "name": "কলকাতা বার্তা", "platform": "Facebook",
             "followers": r.randint(60000, 120000), "stance": "Neutral", "engagement": r.randint(4000, 10000)},
            {"handle": "@BJP_Bangla", "name": "বিজেপি বাংলা", "platform": "X / Twitter",
             "followers": r.randint(80000, 180000), "stance": "Pro-BJP", "engagement": r.randint(5000, 12000)},
            {"handle": "@TMC_Bangla", "name": "তৃণমূল বাংলা", "platform": "X / Twitter",
             "followers": r.randint(70000, 160000), "stance": "Pro-TMC", "engagement": r.randint(4500, 11000)},
            {"handle": "@BanglaYuva", "name": "বাংলা যুব", "platform": "Instagram",
             "followers": r.randint(25000, 65000), "stance": "Neutral", "engagement": r.randint(2000, 6000)},
            {"handle": "@SonarBangla24", "name": "সোনার বাংলা ২৪", "platform": "YouTube",
             "followers": r.randint(100000, 250000), "stance": "Neutral", "engagement": r.randint(6000, 15000)},
            {"handle": "@DeshBangla", "name": "দেশ বাংলা", "platform": "Facebook",
             "followers": r.randint(35000, 75000), "stance": "Pro-LEFT", "engagement": r.randint(2500, 7000)},
            {"handle": "@BengaliVoice_", "name": "বাঙালি কণ্ঠ", "platform": "X / Twitter",
             "followers": r.randint(15000, 45000), "stance": "Regional", "engagement": r.randint(1500, 5000)},
        ],

        "sentiment_by_topic": {
            "Rally/সভা": {"pos": round(r.uniform(40, 60), 1), "neg": round(r.uniform(15, 30), 1)},
            "Economy/অর্থনীতি": {"pos": round(r.uniform(25, 45), 1), "neg": round(r.uniform(25, 40), 1)},
            "Jobs/চাকরি": {"pos": round(r.uniform(20, 40), 1), "neg": round(r.uniform(30, 50), 1)},
            "Identity/পরিচয়": {"pos": round(r.uniform(35, 55), 1), "neg": round(r.uniform(20, 35), 1)},
            "Development/উন্নয়ন": {"pos": round(r.uniform(30, 50), 1), "neg": round(r.uniform(20, 35), 1)},
        },

        "regional_vs_national": {
            "regional_positive": bengali_positive,
            "national_positive": round(r.uniform(35, 55), 1),
            "regional_negative": bengali_negative,
            "national_negative": round(r.uniform(20, 35), 1),
        },

        "key_insight": f"Bengali-language discourse accounts for ~{r.randint(28, 42)}% of total rally mentions. "
                       f"{'Pro-BJP Bengali hashtags are trending higher than opposition' if bengali_positive > 45 else 'Opposition Bengali hashtags are gaining traction'}. "
                       f"Regional sentiment is {'more positive' if bengali_positive > 45 else 'slightly more critical'} than national average.",
    }


def demo_bot_activity():
    """Generate demo bot activity analysis data."""
    r = _seeded_random()
    total_accounts = r.randint(18000, 25000)
    bot_accounts = r.randint(1400, 2200)
    bot_pct = round(bot_accounts / total_accounts * 100, 1)

    pro_bjp_modi = round(r.uniform(35, 48), 1)
    pro_opposition_negative = round(r.uniform(28, 42), 1)
    neutral_bots = round(100 - pro_bjp_modi - pro_opposition_negative, 1)

    return {
        "total_accounts_analyzed": total_accounts,
        "bot_accounts_detected": bot_accounts,
        "bot_percentage": bot_pct,
        "human_accounts": total_accounts - bot_accounts,
        "confidence_score": round(r.uniform(0.82, 0.96), 2),
        "political_inclination": {
            "Pro-BJP / PM Modi": pro_bjp_modi,
            "Anti-BJP (Opposition)": pro_opposition_negative,
            "Neutral / Undetermined": neutral_bots,
        },
        "bot_sentiment": {
            "Positive (Pro-BJP/Modi)": round(r.uniform(30, 45), 1),
            "Negative (Anti-BJP)": round(r.uniform(25, 38), 1),
            "Negative (Anti-Opposition)": round(r.uniform(8, 18), 1),
            "Neutral / Spam": round(r.uniform(10, 20), 1),
        },
        "bot_platforms": {
            "Twitter/X": round(r.uniform(45, 58), 1),
            "Facebook": round(r.uniform(18, 28), 1),
            "Instagram": round(r.uniform(8, 15), 1),
            "YouTube": round(r.uniform(4, 10), 1),
            "Others": round(r.uniform(2, 6), 1),
        },
        "top_bot_hashtags": [
            {"hashtag": "ModiInKolkata", "bot_pct": round(r.uniform(12, 22), 1), "inclination": "Pro-BJP"},
            {"hashtag": "BJP4Bengal", "bot_pct": round(r.uniform(10, 18), 1), "inclination": "Pro-BJP"},
            {"hashtag": "KhelaHobe", "bot_pct": round(r.uniform(15, 25), 1), "inclination": "Pro-TMC"},
            {"hashtag": "ModiGoBack", "bot_pct": round(r.uniform(18, 30), 1), "inclination": "Anti-BJP"},
            {"hashtag": "BengalRejects", "bot_pct": round(r.uniform(20, 35), 1), "inclination": "Anti-BJP"},
            {"hashtag": "ModiMegaRally", "bot_pct": round(r.uniform(8, 15), 1), "inclination": "Pro-BJP"},
        ],
        "bot_activity_timeline": [
            round(r.uniform(2, 6), 1),
            round(r.uniform(3, 7), 1),
            round(r.uniform(4, 8), 1),
            round(r.uniform(5, 10), 1),
            round(r.uniform(8, 15), 1),
            round(r.uniform(12, 22), 1),
            round(r.uniform(10, 18), 1),
        ],
        "key_findings": [
            f"~{bot_pct}% of total accounts show bot-like behavior patterns",
            f"Pro-BJP/Modi bots are {pro_bjp_modi:.0f}% of all bot activity — mostly amplifying rally hashtags",
            f"Anti-BJP opposition bots account for {pro_opposition_negative:.0f}% — spreading negative narratives",
            f"Bot activity spiked {round(r.uniform(180, 320))}% during rally hours vs. pre-rally baseline",
            "Coordinated bot clusters detected on Twitter/X and Facebook targeting rally-related discourse",
        ],
    }
