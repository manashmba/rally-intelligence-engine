"""
JanPulse AI — Dashboard Layout
VIP Executive Command Centre — designed for PM / Governor / Senior Decision Makers.
Every element uses plain English, traffic-light signals, and one-glance verdicts.
"""
from datetime import datetime
try:
    from dash import html, dcc
    import dash_bootstrap_components as dbc
except ImportError:
    pass

# ─── Party colors ─────────────────────────────────────────────────────
PARTY_COLORS = {"BJP": "#FF6B00", "TMC": "#00BCD4", "LEFT": "#E53935",
                "Congress": "#1565C0", "Neutral": "#78909C", "Others": "#7E57C2"}

# ═══════════════════════════════════════════════════════════════════════
#  REUSABLE EXECUTIVE COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def _kpi_card(title, val_id, border, sub_id=None, sub_text=None, meaning_id=None):
    """KPI card with optional plain-English meaning label underneath."""
    body = [
        html.P(title, className="text-muted mb-1",
               style={"fontSize": "0.7rem", "textTransform": "uppercase",
                       "letterSpacing": "1.2px", "fontWeight": "600"}),
        html.H2(id=val_id, className="mb-0",
                 style={"fontWeight": "800", "color": "white", "fontSize": "1.8rem"}),
    ]
    if sub_id:
        body.append(html.Small(id=sub_id, className="text-muted"))
    elif sub_text:
        body.append(html.Small(sub_text, className="text-muted",
                               style={"fontSize": "0.7rem"}))
    if meaning_id:
        body.append(html.Div(id=meaning_id,
                             style={"fontSize": "0.72rem", "marginTop": "6px",
                                    "lineHeight": "1.3", "fontStyle": "italic"}))
    return dbc.Card(
        dbc.CardBody(body, style={"padding": "14px 18px"}),
        className=f"bg-dark border-{border}",
        style={"borderLeft": "4px solid", "borderRadius": "10px",
               "boxShadow": "0 2px 12px rgba(0,0,0,0.3)"})


def _sm_stat_card(title, val_id, delta_id, border="secondary"):
    return dbc.Card(dbc.CardBody([
        html.P(title, className="text-muted mb-1",
               style={"fontSize": "0.68rem", "textTransform": "uppercase",
                       "letterSpacing": "1px", "fontWeight": "600"}),
        html.H3(id=val_id, className="mb-0 text-light",
                 style={"fontWeight": "700"}),
        html.Small(id=delta_id, className="text-success"),
    ], style={"padding": "12px 14px"}),
        className=f"bg-dark border-{border}",
        style={"borderTop": "3px solid", "borderRadius": "10px",
               "boxShadow": "0 2px 8px rgba(0,0,0,0.2)"})


def _section_header(icon, title, plain_english, section_num=None, live=False):
    """Section header with numbering, title, plain English subtitle, and optional LIVE badge."""
    num_badge = ""
    if section_num:
        num_badge = html.Span(f"Section {section_num}",
                              className="me-2",
                              style={"fontSize": "0.65rem", "background": "#37474F",
                                     "padding": "2px 8px", "borderRadius": "10px",
                                     "color": "#90A4AE", "fontWeight": "600",
                                     "textTransform": "uppercase", "letterSpacing": "1px"})
    live_badge = ""
    if live:
        live_badge = html.Span("LIVE",
                               style={"fontSize": "0.55rem", "background": "#27AE60",
                                      "color": "white", "padding": "2px 8px",
                                      "borderRadius": "10px", "marginLeft": "10px",
                                      "fontWeight": "700", "letterSpacing": "1.5px",
                                      "verticalAlign": "middle",
                                      "boxShadow": "0 0 8px rgba(39,174,96,0.5)"})
    return dbc.Row([dbc.Col([
        html.Div([
            num_badge,
            html.H3([html.Span(f"{icon} ", style={"fontSize": "1.3rem"}), title],
                     className="text-light mb-0 d-inline",
                     style={"fontSize": "1.25rem", "fontWeight": "700"}),
            live_badge,
        ], className="mb-1"),
        html.P([
            html.Span("In plain terms: ", style={"color": "#FBBF24", "fontWeight": "600"}),
            html.Span(plain_english, style={"color": "#B0BEC5"}),
        ], className="mb-0", style={"fontSize": "0.82rem"}),
    ])], className="mb-3")


def _chart_card(title, graph_id, border="dark", subtitle=None, height=None):
    hdr = [html.Span(title, className="fw-bold")]
    if subtitle:
        hdr.append(html.Small(f" — {subtitle}", className="text-muted ms-2"))
    return dbc.Card([
        dbc.CardHeader(hdr, style={"padding": "8px 14px", "fontSize": "0.85rem"}),
        dbc.CardBody(dcc.Graph(id=graph_id, config={"displayModeBar": False}),
                     style={"padding": "8px"})
    ], className=f"bg-dark border-{border}",
       style={"borderRadius": "10px", "boxShadow": "0 2px 12px rgba(0,0,0,0.25)"})


def _insight_box(insight_id, icon="💡", border_color="#4FC3F7"):
    """Executive quick-read summary box — plain English interpretation."""
    return dbc.Row([dbc.Col(html.Div(
        id=insight_id,
        style={"padding": "12px 18px", "background": "rgba(79,195,247,0.04)",
               "borderRadius": "10px", "borderLeft": f"4px solid {border_color}",
               "fontSize": "0.82rem", "lineHeight": "1.7", "color": "#E2E8F0",
               "boxShadow": "0 1px 6px rgba(0,0,0,0.15)"}
    ), width=12)], className="mb-4")


def _traffic_light_card(title, signal_id, text_id, subtitle=""):
    """Large traffic-light signal card for executive summary."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div(id=signal_id,
                         style={"width": "18px", "height": "18px",
                                "borderRadius": "50%", "display": "inline-block",
                                "marginRight": "10px", "verticalAlign": "middle",
                                "boxShadow": "0 0 8px rgba(255,255,255,0.3)"}),
                html.Span(title, style={"fontSize": "0.78rem", "fontWeight": "700",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "1.5px", "color": "#90A4AE"}),
            ], className="mb-2"),
            html.Div(id=text_id,
                     style={"fontSize": "1.15rem", "fontWeight": "700",
                            "lineHeight": "1.4", "color": "white",
                            "minHeight": "52px"}),
            html.Small(subtitle, className="text-muted",
                       style={"fontSize": "0.68rem"}) if subtitle else None,
        ], style={"padding": "18px 20px"})
    ], className="bg-dark",
       style={"borderRadius": "12px", "border": "1px solid #37474F",
              "boxShadow": "0 4px 20px rgba(0,0,0,0.4)"})


# ═══════════════════════════════════════════════════════════════════════
#  MAIN LAYOUT
# ═══════════════════════════════════════════════════════════════════════

def build_layout():
    """Build the VIP executive dashboard layout."""
    return dbc.Container([

        # ══════════ CONFIDENTIAL HEADER BAR ══════════
        html.Div([
            html.Div([
                html.Span("CONFIDENTIAL", style={
                    "fontSize": "0.6rem", "fontWeight": "800",
                    "letterSpacing": "3px", "color": "#EF5350",
                    "background": "rgba(239,83,80,0.1)", "padding": "3px 12px",
                    "borderRadius": "3px", "border": "1px solid rgba(239,83,80,0.3)"}),
                html.Span(" • RALLY INTELLIGENCE COMMAND CENTRE • ",
                          style={"fontSize": "0.6rem", "color": "#546E7A",
                                 "letterSpacing": "2px", "margin": "0 8px"}),
                html.Span("LIVE MONITORING",
                          style={"fontSize": "0.6rem", "fontWeight": "700",
                                 "letterSpacing": "2px", "color": "#66BB6A"}),
            ], style={"textAlign": "center", "padding": "6px 0"}),
        ], style={"borderBottom": "1px solid #263238",
                  "background": "rgba(0,0,0,0.3)", "marginBottom": "12px"}),

        # ══════════ MAIN HEADER ══════════
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Img(src="https://img.icons8.com/fluency/48/spy-agency.png",
                             style={"height": "36px", "marginRight": "12px",
                                    "verticalAlign": "middle", "opacity": "0.9"}),
                    html.Span("JanPulse AI",
                              style={"fontWeight": "800", "color": "#4FC3F7",
                                     "fontSize": "1.9rem", "verticalAlign": "middle"}),
                ], style={"display": "inline-flex", "alignItems": "center"}),
                html.P("India's Public Mood Analysis Engine — Executive Briefing Dashboard",
                       className="text-muted mb-0",
                       style={"fontSize": "0.82rem", "marginTop": "4px",
                              "paddingLeft": "48px"}),
            ], width=8),
            dbc.Col([
                html.Div(id="live-clock", className="text-end text-info",
                         style={"fontSize": "1.5rem", "fontWeight": "700"}),
                html.Div(id="phase-badge", className="text-end"),
                html.Div("Auto-refreshes every 30 seconds",
                         className="text-end text-muted",
                         style={"fontSize": "0.65rem", "marginTop": "4px"}),
            ], width=4),
        ], className="mb-3 mt-1 pb-2",
           style={"borderBottom": "2px solid #263238"}),

        # ══════════ EXECUTIVE TRAFFIC LIGHT SUMMARY ══════════
        # The first thing a PM/Governor sees — 3 big traffic-light cards
        html.Div([
            html.Span("⚡ ", style={"fontSize": "1rem"}),
            html.Span("SITUATION AT A GLANCE",
                      style={"fontSize": "0.75rem", "fontWeight": "800",
                             "letterSpacing": "2.5px", "color": "#B0BEC5"}),
            html.Span(" — read only this section for a 10-second briefing",
                      style={"fontSize": "0.72rem", "color": "#546E7A",
                             "fontStyle": "italic"}),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col(_traffic_light_card(
                "Overall Situation", "exec-situation-signal", "exec-situation-text",
                "Based on sentiment + bot activity + polarization"), width=4),
            dbc.Col(_traffic_light_card(
                "Public Mood Towards Rally", "exec-mood-signal", "exec-mood-text",
                "Are people reacting positively or negatively?"), width=4),
            dbc.Col(_traffic_light_card(
                "Threat / Risk Level", "exec-threat-signal", "exec-threat-text",
                "Bot manipulation + negative campaigns + opposition intensity"), width=4),
        ], className="mb-4 g-3"),

        # ══════════ KEY NUMBERS (KPI CARDS WITH MEANINGS) ══════════
        html.Div([
            html.Span("📊 ", style={"fontSize": "1rem"}),
            html.Span("KEY NUMBERS",
                      style={"fontSize": "0.72rem", "fontWeight": "700",
                             "letterSpacing": "2px", "color": "#90A4AE"}),
            html.Span(" — what each number means is written below it",
                      style={"fontSize": "0.7rem", "color": "#546E7A",
                             "fontStyle": "italic"}),
        ], className="mb-2"),
        dbc.Row([
            dbc.Col(_kpi_card("Rally Mood Score", "kpi-mood", "primary",
                              sub_text="/ 100", meaning_id="kpi-mood-meaning"), width=2),
            dbc.Col(_kpi_card("Total Mentions", "kpi-mentions", "info",
                              meaning_id="kpi-mentions-meaning"), width=2),
            dbc.Col(_kpi_card("Positive %", "kpi-positive", "success",
                              meaning_id="kpi-positive-meaning"), width=2),
            dbc.Col(_kpi_card("Negative %", "kpi-negative", "danger",
                              meaning_id="kpi-negative-meaning"), width=2),
            dbc.Col(_kpi_card("Bot Suspicion %", "kpi-bots", "warning",
                              meaning_id="kpi-bots-meaning"), width=2),
            dbc.Col(_kpi_card("Leader Favourability", "kpi-favour", "primary",
                              meaning_id="kpi-favour-meaning"), width=2),
        ], className="mb-4 g-2"),

        # ── MAIN CHARTS ROW ──
        _section_header("📈", "Sentiment & Platform Overview",
                        "How are people feeling, and where is the conversation happening?",
                        section_num="1"),
        dbc.Row([
            dbc.Col(_chart_card("Public Mood Split", "sentiment-pie",
                                subtitle="positive vs negative vs neutral"), width=4),
            dbc.Col(_chart_card("Emotional Reactions", "emotion-bar",
                                subtitle="what emotions are people expressing?"), width=4),
            dbc.Col(_chart_card("Where People Are Talking", "platform-bar",
                                subtitle="Twitter, Facebook, Instagram, etc."), width=4),
        ], className="mb-2 g-2"),
        _insight_box("insight-main-charts", "📊", "#4FC3F7"),

        # ══════════ ADVANCED SENTIMENT ANALYSIS ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("🧠", "Deep Sentiment Analysis",
                        "Beyond just positive/negative — what specific emotions are people showing?",
                        section_num="2"),
        dbc.Row([
            dbc.Col(_chart_card("Detailed Emotion Breakdown", "adv-sentiment-pie", "info",
                                "10 different emotions detected"), width=6),
            dbc.Col(_chart_card("Overall Direction Meter", "polarity-gauge", "warning",
                                "is the mood tilting positive or negative?"), width=3),
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.Span("Numbers Behind Each Emotion", className="fw-bold")],
                               style={"padding": "8px 14px", "fontSize": "0.85rem"}),
                dbc.CardBody(id="sentiment-breakdown-stats",
                             style={"maxHeight": "480px", "overflow": "auto", "padding": "10px"})
            ], className="bg-dark border-secondary",
               style={"borderRadius": "10px"}), width=3),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(_chart_card("Mood Trend — Last 7 Days", "sentiment-timeline", "info",
                                "is the mood getting better or worse?"), width=7),
            dbc.Col(_chart_card("Emotion Radar Map", "emotion-radar", "primary",
                                "multi-dimensional view of emotions"), width=5),
        ], className="mb-2 g-2"),
        _insight_box("insight-adv-sentiment", "🧠", "#F39C12"),

        # ══════════ SOCIAL MEDIA SUMMARY ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("📱", "Social Media Reach & Impact",
                        "How far is the rally message spreading across social media platforms?",
                        section_num="3"),
        dbc.Row([
            dbc.Col(_sm_stat_card("MENTIONS", "sm-mentions-val", "sm-mentions-delta", "info"), width=2),
            dbc.Col(_sm_stat_card("SM REACH", "sm-reach-val", "sm-reach-delta", "success"), width=2),
            dbc.Col(_sm_stat_card("INTERACTIONS", "sm-int-val", "sm-int-delta", "warning"), width=2),
            dbc.Col(_sm_stat_card("SM LIKES", "sm-likes-val", "sm-likes-delta", "primary"), width=2),
            dbc.Col(_sm_stat_card("POSITIVE", "sm-pos-val", "sm-pos-delta", "success"), width=2),
            dbc.Col(_sm_stat_card("NEGATIVE", "sm-neg-val", "sm-neg-delta", "danger"), width=2),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(_sm_stat_card("UGC", "sm-ugc-val", "sm-ugc-delta"), width=2),
            dbc.Col(_sm_stat_card("VIDEOS", "sm-vid-val", "sm-vid-delta"), width=2),
            dbc.Col(_sm_stat_card("NON-SOCIAL REACH", "sm-ns-reach-val", "sm-ns-reach-delta"), width=2),
            dbc.Col(_sm_stat_card("NON-SOCIAL MENTIONS", "sm-ns-val", "sm-ns-delta"), width=2),
            dbc.Col(_sm_stat_card("VIRAL POSTS", "sm-viral-val", "sm-viral-delta", "primary"), width=2),
            dbc.Col(_sm_stat_card("AVG ENGAGEMENT", "sm-avg-eng-val", "sm-avg-eng-delta", "info"), width=2),
        ], className="mb-4 g-2"),
        dbc.Row([
            dbc.Col(_chart_card("📈 How Mentions Are Growing", "mentions-timeline", "info",
                                "daily volume of people talking about the rally"), width=12),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(_chart_card("📡 How Far The Message Reached", "reach-timeline", "success",
                                "total impressions over time"), width=7),
            dbc.Col(_chart_card("Which Platform Is Contributing Most", "platform-pie", "secondary",
                                "share of conversations"), width=5),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(_chart_card("🔥 Engagement Heatmap", "eng-heatmap", "warning",
                                "which platform had most activity on which day?"), width=12),
        ], className="mb-2 g-2"),
        _insight_box("insight-social-media", "📱", "#27AE60"),

        # ══════════ TOP 8 POPULAR MENTIONS ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("🔥", "Most Viral Posts",
                        "These 8 posts got the most attention — what went viral and why?",
                        section_num="4"),
        dbc.Row([dbc.Col(id="popular-mentions-grid", width=12)], className="mb-4"),
        _insight_box("insight-popular-mentions", "🔥", "#E74C3C"),

        # ══════════ TOP SOCIAL MEDIA MENTIONS TABLE ══════════
        _section_header("📢", "Top Voices & Trending Profiles",
                        "Who are the most influential accounts talking about this rally? Real-time across all platforms.",
                        section_num="5", live=True),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody(id="sm-mentions-table", style={"padding": "0"})
            ], className="bg-dark border-info",
               style={"borderRadius": "10px"}), width=12),
        ], className="mb-4"),

        # ══════════ HASHTAGS + ALERTS ROW ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("🏷️", "Trending Topics & Live Alerts",
                        "Which hashtags are trending, who are the key voices, and are there any alerts? Updated every 30 seconds.",
                        section_num="6", live=True),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.Span("Top Hashtags", className="fw-bold"),
                                html.Small(" — trending rally topics", className="text-muted ms-2")]),
                dbc.CardBody(id="hashtag-list")
            ], className="bg-dark", style={"borderRadius": "10px"}), width=4),
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.Span("Key Influencers", className="fw-bold"),
                                html.Small(" — most active voices", className="text-muted ms-2")]),
                dbc.CardBody(id="influencer-list")
            ], className="bg-dark", style={"borderRadius": "10px"}), width=4),
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.Span("⚠️ Live Alerts", className="text-danger fw-bold"),
                                html.Small(" — items needing attention", className="text-muted ms-2")]),
                dbc.CardBody(id="alert-feed",
                             style={"maxHeight": "280px", "overflow": "auto"})
            ], className="bg-dark border-danger",
               style={"borderRadius": "10px"}), width=4),
        ], className="mb-3 g-2"),

        # Trending Topics + Real-Time Alerts (cross-platform)
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([
                    html.Span("📈 Top Trending Topics ", className="fw-bold",
                              style={"color": "#4FC3F7"}),
                    html.Span("LIVE", style={"fontSize": "0.55rem", "background": "#27AE60",
                              "color": "white", "padding": "2px 8px", "borderRadius": "10px",
                              "marginLeft": "8px", "fontWeight": "700", "letterSpacing": "1px",
                              "boxShadow": "0 0 8px rgba(39,174,96,0.4)"}),
                    html.Br(),
                    html.Small("Real-time across X/Twitter, Facebook, Instagram, YouTube, Reddit, News",
                               className="text-muted", style={"fontSize": "0.7rem"}),
                ], style={"padding": "10px 14px", "fontSize": "0.85rem",
                          "borderBottom": "2px solid rgba(79,195,247,0.3)"}),
                dbc.CardBody(id="trending-topics-list",
                             style={"maxHeight": "520px", "overflow": "auto", "padding": "12px"})
            ], className="bg-dark border-info",
               style={"borderRadius": "10px",
                      "boxShadow": "0 2px 12px rgba(0,0,0,0.25)"}), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader([
                    html.Span("🚨 Live Intelligence Alerts ", className="fw-bold",
                              style={"color": "#EF5350"}),
                    html.Span("LIVE", style={"fontSize": "0.55rem", "background": "#EF5350",
                              "color": "white", "padding": "2px 8px", "borderRadius": "10px",
                              "marginLeft": "8px", "fontWeight": "700", "letterSpacing": "1px",
                              "boxShadow": "0 0 8px rgba(239,83,80,0.4)"}),
                    html.Br(),
                    html.Small("Real-time alerts from all social & digital media networks",
                               className="text-muted", style={"fontSize": "0.7rem"}),
                ], style={"padding": "10px 14px", "fontSize": "0.85rem",
                          "borderBottom": "2px solid rgba(239,83,80,0.3)"}),
                dbc.CardBody(id="live-alerts-feed",
                             style={"maxHeight": "520px", "overflow": "auto", "padding": "12px"})
            ], className="bg-dark border-danger",
               style={"borderRadius": "10px",
                      "boxShadow": "0 2px 12px rgba(0,0,0,0.25)"}), width=6),
        ], className="mb-2 g-2"),
        _insight_box("insight-hashtags-alerts", "🏷️", "#F39C12"),

        # ══════════ TOP 20 POSITIVE / NEGATIVE INFLUENCERS ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("👥", "Influencer Analysis — Friends vs Critics",
                        "Who is supporting the rally narrative, and who is opposing it? Real-time across all social & digital media.",
                        section_num="7", live=True),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("🟢 Top 20 Supportive Voices",
                                  className="text-success fw-bold"),
                        html.Small(" — accounts speaking positively",
                                   className="text-muted ms-2")],
                        style={"padding": "10px 14px", "fontSize": "0.85rem"}),
                    dbc.CardBody(id="pos-inf-table",
                                 style={"maxHeight": "500px", "overflow": "auto",
                                        "padding": "0"})
                ], className="bg-dark border-success",
                   style={"borderRadius": "10px"})
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("🔴 Top 20 Critical Voices",
                                  className="text-danger fw-bold"),
                        html.Small(" — accounts speaking negatively",
                                   className="text-muted ms-2")],
                        style={"padding": "10px 14px", "fontSize": "0.85rem"}),
                    dbc.CardBody(id="neg-inf-table",
                                 style={"maxHeight": "500px", "overflow": "auto",
                                        "padding": "0"})
                ], className="bg-dark border-danger",
                   style={"borderRadius": "10px"})
            ], width=6),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(_chart_card("Supportive Voice Share", "pos-inf-pie", "success",
                                "who has the most influence among supporters?"), width=6),
            dbc.Col(_chart_card("Critical Voice Share", "neg-inf-pie", "danger",
                                "who has the most influence among critics?"), width=6),
        ], className="mb-2 g-2"),
        _insight_box("insight-influencers", "👥", "#27AE60"),

        # ══════════ POLITICAL LEANING ANALYSIS ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("🏛️", "Political Alignment Map",
                        "Which party's supporters are most active online? How do they feel about the rally? Real-time stance tracking.",
                        section_num="8", live=True),
        dbc.Row([
            dbc.Col(_chart_card("Influencer Political Alignment", "inf-party-pie", "warning",
                                "which party do key voices lean towards?"), width=6),
            dbc.Col(_chart_card("Hashtag Political Alignment", "ht-party-pie", "warning",
                                "which party do trending topics favour?"), width=6),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.Span("🧑‍💼 Influencer Party Stance", className="fw-bold")],
                               style={"padding": "8px 14px", "fontSize": "0.85rem"}),
                dbc.CardBody(id="inf-stance-tbl",
                             style={"maxHeight": "400px", "overflow": "auto", "padding": "0"})
            ], className="bg-dark border-secondary",
               style={"borderRadius": "10px"}), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader([html.Span("#️⃣ Hashtag Party Stance", className="fw-bold")],
                               style={"padding": "8px 14px", "fontSize": "0.85rem"}),
                dbc.CardBody(id="ht-stance-tbl",
                             style={"maxHeight": "400px", "overflow": "auto", "padding": "0"})
            ], className="bg-dark border-secondary",
               style={"borderRadius": "10px"}), width=6),
        ], className="mb-3 g-2"),
        dbc.Row([
            dbc.Col(_chart_card("Party-wise Sentiment", "party-sent-bar", "info",
                                "how positive/negative is each party's online mood?"), width=12),
        ], className="mb-2 g-2"),
        _insight_box("insight-political", "🏛️", "#7E57C2"),

        # ══════════ BOT ACTIVITY INTELLIGENCE ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("🤖", "Fake Account (Bot) Analysis",
                        "Are automated fake accounts trying to manipulate the conversation? Who are they working for?",
                        section_num="9"),
        # Executive explainer box
        dbc.Row([dbc.Col(html.Div([
            html.Div([
                html.Span("⚠️ ", style={"fontSize": "1.1rem"}),
                html.Strong("What are Bots? ",
                            style={"color": "#FBBF24", "fontSize": "0.9rem"}),
            ], className="mb-1"),
            html.Span("'Bots' are ", style={"color": "#E2E8F0"}),
            html.Strong("automated fake accounts", style={"color": "#EF5350"}),
            html.Span(" that post thousands of messages to artificially make something look popular or unpopular. "
                       "Below we show whether these fake accounts are working ",
                       style={"color": "#E2E8F0"}),
            html.Strong("FOR BJP/PM Modi ", style={"color": "#FF6B00", "fontSize": "0.95rem"}),
            html.Span("or ", style={"color": "#E2E8F0"}),
            html.Strong("AGAINST BJP (for Opposition) ", style={"color": "#00BCD4", "fontSize": "0.95rem"}),
            html.Span(". This helps separate ", style={"color": "#E2E8F0"}),
            html.Strong("genuine public opinion", style={"color": "#66BB6A"}),
            html.Span(" from ", style={"color": "#E2E8F0"}),
            html.Strong("manufactured noise", style={"color": "#EF5350"}),
            html.Span(".", style={"color": "#E2E8F0"}),
        ], style={"padding": "14px 20px", "background": "rgba(251,191,36,0.06)",
                  "borderRadius": "12px", "borderLeft": "4px solid #FBBF24",
                  "fontSize": "0.85rem", "lineHeight": "1.6",
                  "boxShadow": "0 2px 12px rgba(0,0,0,0.2)"}), width=12)], className="mb-3"),

        # Bot KPI Cards
        dbc.Row([
            dbc.Col(_kpi_card("Accounts Analyzed", "bot-total-accounts", "info"), width=2),
            dbc.Col(_kpi_card("Bots Detected", "bot-detected", "danger"), width=2),
            dbc.Col(_kpi_card("Bot Detection Rate", "bot-detection-rate", "warning"), width=2),
            dbc.Col(_kpi_card("Pro-BJP/Modi Bots", "bot-pro-bjp", "warning",
                              sub_text="of all bots"), width=2),
            dbc.Col(_kpi_card("Anti-BJP Opp. Bots", "bot-anti-bjp", "info",
                              sub_text="of all bots"), width=2),
            dbc.Col(_kpi_card("Neutral Bots", "bot-neutral", "secondary",
                              sub_text="of all bots"), width=2),
        ], className="mb-3 g-2"),

        # Bot Charts
        dbc.Row([
            dbc.Col(_chart_card("Who Are Bots Supporting?", "bot-inclination-pie", "warning",
                                "political inclination of fake accounts"), width=4),
            dbc.Col(_chart_card("What Are Bots Saying?", "bot-sentiment-pie", "danger",
                                "positive/negative breakdown of bot messages"), width=4),
            dbc.Col(_chart_card("Where Are Bots Most Active?", "bot-platform-bar", "info",
                                "which platforms have the most bots?"), width=4),
        ], className="mb-3 g-2"),

        # Bot Timeline + Hashtag Analysis
        dbc.Row([
            dbc.Col(_chart_card("Bot Activity Over Time", "bot-timeline", "warning",
                                "is fake account activity increasing or decreasing?"), width=7),
            dbc.Col(dbc.Card([
                dbc.CardHeader([
                    html.Span("Bot-Infiltrated Hashtags", className="fw-bold"),
                    html.Small(" — how much of each hashtag is fake?",
                               className="text-muted ms-2")],
                    style={"padding": "8px 14px", "fontSize": "0.85rem"}),
                dbc.CardBody(id="bot-hashtag-list",
                             style={"maxHeight": "320px", "overflow": "auto",
                                    "padding": "10px"})
            ], className="bg-dark border-warning",
               style={"borderRadius": "10px"}), width=5),
        ], className="mb-3 g-2"),

        # Key Findings
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([
                    html.Span("🔑 ", style={"fontSize": "1.1rem"}),
                    html.Span("KEY FINDINGS — Read This First",
                              className="fw-bold",
                              style={"color": "#FBBF24", "fontSize": "0.95rem"})],
                    style={"padding": "12px 18px",
                           "background": "rgba(251,191,36,0.08)",
                           "borderBottom": "2px solid rgba(251,191,36,0.3)"}),
                dbc.CardBody(id="bot-key-findings", style={"padding": "16px 20px"})
            ], className="bg-dark border-warning",
               style={"borderWidth": "2px", "borderRadius": "12px",
                      "boxShadow": "0 4px 20px rgba(251,191,36,0.1)"}), width=12),
        ], className="mb-4 g-2"),

        # ══════════ REGIONAL BENGALI INTELLIGENCE ══════════
        html.Hr(style={"borderColor": "#263238", "margin": "8px 0 16px"}),
        _section_header("🇮🇳", "Regional Bengali Pulse — আঞ্চলিক বাংলা বিশ্লেষণ",
                        "What is Bengal's own social media saying? Bengali hashtags, local influencers, and regional sentiment",
                        section_num="10"),
        # Bengali context explainer
        dbc.Row([dbc.Col(html.Div([
            html.Div([
                html.Span("🗣️ ", style={"fontSize": "1.1rem"}),
                html.Strong("Why This Section Matters: ",
                            style={"color": "#FF6B00", "fontSize": "0.9rem"}),
            ], className="mb-1"),
            html.Span("National-level data often misses ", style={"color": "#E2E8F0"}),
            html.Strong("local Bengali sentiment", style={"color": "#FBBF24"}),
            html.Span(". This section tracks conversations happening in ", style={"color": "#E2E8F0"}),
            html.Strong("Bengali language", style={"color": "#00BCD4"}),
            html.Span(", ", style={"color": "#E2E8F0"}),
            html.Strong("regional hashtags", style={"color": "#00BCD4"}),
            html.Span(", and ", style={"color": "#E2E8F0"}),
            html.Strong("local influencer handles", style={"color": "#00BCD4"}),
            html.Span(" — giving a true picture of ground-level mood in West Bengal.",
                       style={"color": "#E2E8F0"}),
        ], style={"padding": "14px 20px", "background": "rgba(255,107,0,0.05)",
                  "borderRadius": "12px", "borderLeft": "4px solid #FF6B00",
                  "fontSize": "0.85rem", "lineHeight": "1.6",
                  "boxShadow": "0 2px 12px rgba(0,0,0,0.2)"}), width=12)], className="mb-3"),

        # Regional KPI summary row
        dbc.Row([
            dbc.Col(_kpi_card("Bengali Mentions", "reg-bengali-mentions", "info",
                              meaning_id="reg-bengali-mentions-meaning"), width=3),
            dbc.Col(_kpi_card("Bengali Positive %", "reg-bengali-positive", "success",
                              meaning_id="reg-bengali-positive-meaning"), width=3),
            dbc.Col(_kpi_card("Bengali Negative %", "reg-bengali-negative", "danger"), width=3),
            dbc.Col(_kpi_card("Regional Reach", "reg-bengali-reach", "primary"), width=3),
        ], className="mb-3 g-2"),

        # Bengali Hashtags + Bengali Influencers side by side
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader([
                    html.Span("🏷️ Trending Bengali Hashtags", className="fw-bold",
                              style={"color": "#FF6B00"}),
                    html.Small(" — আঞ্চলিক হ্যাশট্যাগ", className="text-muted ms-2",
                               style={"fontSize": "0.75rem"})],
                    style={"padding": "10px 14px", "fontSize": "0.85rem",
                           "borderBottom": "2px solid rgba(255,107,0,0.3)"}),
                dbc.CardBody(id="reg-bengali-hashtags",
                             style={"maxHeight": "480px", "overflow": "auto",
                                    "padding": "12px"})
            ], className="bg-dark border-warning",
               style={"borderRadius": "10px",
                      "boxShadow": "0 2px 12px rgba(0,0,0,0.25)"}), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader([
                    html.Span("👤 Key Bengali Influencers", className="fw-bold",
                              style={"color": "#00BCD4"}),
                    html.Small(" — প্রভাবশালী ব্যক্তিত্ব", className="text-muted ms-2",
                               style={"fontSize": "0.75rem"})],
                    style={"padding": "10px 14px", "fontSize": "0.85rem",
                           "borderBottom": "2px solid rgba(0,188,212,0.3)"}),
                dbc.CardBody(id="reg-bengali-influencers",
                             style={"maxHeight": "480px", "overflow": "auto",
                                    "padding": "0"})
            ], className="bg-dark border-info",
               style={"borderRadius": "10px",
                      "boxShadow": "0 2px 12px rgba(0,0,0,0.25)"}), width=6),
        ], className="mb-3 g-2"),

        # Regional Sentiment Pie + Platform split
        dbc.Row([
            dbc.Col(_chart_card("Bengali Sentiment Split", "reg-bengali-sentiment-pie", "warning",
                                "mood of Bengali-language conversations"), width=4),
            dbc.Col(_chart_card("Bengali Topic Cloud", "reg-bengali-topics-bar", "info",
                                "most discussed topics in Bengali"), width=4),
            dbc.Col(_chart_card("Regional vs National Mood", "reg-vs-national-bar", "primary",
                                "how does Bengal differ from the national picture?"), width=4),
        ], className="mb-2 g-2"),
        _insight_box("insight-regional-bengali", "🇮🇳", "#FF6B00"),

        # ══════════ FOOTER ══════════
        html.Div([
            html.Hr(style={"borderColor": "#263238"}),
            html.P([
                html.Span("JanPulse AI", style={"fontWeight": "700", "color": "#4FC3F7"}),
                html.Span(" • Powered by AI-driven NLP & Social Media Analytics • ",
                          style={"color": "#546E7A"}),
                html.Span("CONFIDENTIAL — For Authorized Personnel Only",
                          style={"color": "#EF5350", "fontWeight": "600",
                                 "fontSize": "0.7rem", "letterSpacing": "1px"}),
            ], style={"textAlign": "center", "fontSize": "0.75rem",
                      "padding": "8px 0"}),
        ]),

        # ── Auto-refresh ──
        dcc.Interval(id="refresh-interval", interval=30000, n_intervals=0),
        dcc.Store(id="kpi-store", data={}),

    ], fluid=True, className="bg-dark text-light",
       style={"minHeight": "100vh", "paddingBottom": "40px",
              "fontFamily": "'Segoe UI', 'Inter', -apple-system, sans-serif"})
