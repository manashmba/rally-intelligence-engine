"""
JanPulse AI — Dashboard Server
Real-time web dashboard using Dash/Plotly for the command centre view.
"""
import os, sys, random
from datetime import datetime, timedelta
from loguru import logger

try:
    import dash
    from dash import html, dcc, callback
    from dash.dependencies import Input, Output
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    HAS_DASH = True
except ImportError:
    HAS_DASH = False
    logger.warning("Dash not installed; dashboard disabled")

from engine.models import KPISnapshot, RallyPhase, SentimentShare
from engine.dashboard.layout import build_layout
from engine.dashboard.demo_data import (
    demo_dates, demo_advanced_sentiment, demo_popular_mentions,
    demo_sm_mentions_table, demo_trending_hashtags, demo_trending_topics,
    demo_live_alerts, demo_inf_stance,
    demo_ht_stance, demo_bot_activity, demo_regional_bengali,
    ADV_COLORS, ADV_EMOJIS, PARTY_COLORS, PARTY_BADGE, PLAT_COLORS,
    BOT_INCLINATION_COLORS, BOT_SENTIMENT_COLORS, BENGALI_HASHTAG_COLORS,
)

# ─── Chart style constants ────────────────────────────────────────────
_BG = "rgba(0,0,0,0)"
_MARGIN_SM = dict(t=20, b=30, l=40, r=20)
_MARGIN_MD = dict(t=20, b=40, l=50, r=20)


def _fig_layout(fig, h=250, margin=None, **kw):
    fig.update_layout(paper_bgcolor=_BG, plot_bgcolor=_BG, font_color="white",
                      height=h, margin=margin or _MARGIN_SM, **kw)
    return fig


def create_app(kpi_store: list = None):
    if not HAS_DASH:
        logger.error("Dash required. pip install dash dash-bootstrap-components")
        return None

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE],
                    title="JanPulse AI")
    app.layout = build_layout()

    # Build the full callback outputs list
    outputs = [
        # 0-5: KPI values
        Output("kpi-mood", "children"), Output("kpi-mentions", "children"),
        Output("kpi-positive", "children"), Output("kpi-negative", "children"),
        Output("kpi-bots", "children"), Output("kpi-favour", "children"),
        # 6-8: main charts
        Output("sentiment-pie", "figure"), Output("emotion-bar", "figure"),
        Output("platform-bar", "figure"),
        # 9-13: panels
        Output("hashtag-list", "children"), Output("influencer-list", "children"),
        Output("alert-feed", "children"), Output("live-clock", "children"),
        Output("phase-badge", "children"),
        # 14-15: top 20 influencer tables
        Output("pos-inf-table", "children"), Output("neg-inf-table", "children"),
        # 16-20: advanced sentiment
        Output("adv-sentiment-pie", "figure"), Output("polarity-gauge", "figure"),
        Output("sentiment-breakdown-stats", "children"),
        Output("sentiment-timeline", "figure"), Output("emotion-radar", "figure"),
        # 21-44: social media summary (12 stat cards × 2 = 24 outputs)
        Output("sm-mentions-val", "children"), Output("sm-mentions-delta", "children"),
        Output("sm-reach-val", "children"), Output("sm-reach-delta", "children"),
        Output("sm-int-val", "children"), Output("sm-int-delta", "children"),
        Output("sm-likes-val", "children"), Output("sm-likes-delta", "children"),
        Output("sm-pos-val", "children"), Output("sm-pos-delta", "children"),
        Output("sm-neg-val", "children"), Output("sm-neg-delta", "children"),
        Output("sm-ugc-val", "children"), Output("sm-ugc-delta", "children"),
        Output("sm-vid-val", "children"), Output("sm-vid-delta", "children"),
        Output("sm-ns-reach-val", "children"), Output("sm-ns-reach-delta", "children"),
        Output("sm-ns-val", "children"), Output("sm-ns-delta", "children"),
        Output("sm-viral-val", "children"), Output("sm-viral-delta", "children"),
        Output("sm-avg-eng-val", "children"), Output("sm-avg-eng-delta", "children"),
        # 45-48: SM charts
        Output("mentions-timeline", "figure"), Output("reach-timeline", "figure"),
        Output("platform-pie", "figure"), Output("eng-heatmap", "figure"),
        # 49-50: popular mentions + SM mentions table
        Output("popular-mentions-grid", "children"),
        Output("sm-mentions-table", "children"),
        # 51-52: influencer pies
        Output("pos-inf-pie", "figure"), Output("neg-inf-pie", "figure"),
        # 53-57: political leaning
        Output("inf-party-pie", "figure"), Output("ht-party-pie", "figure"),
        Output("inf-stance-tbl", "children"), Output("ht-stance-tbl", "children"),
        Output("party-sent-bar", "figure"),
        # 58-63: Bot activity KPIs
        Output("bot-total-accounts", "children"), Output("bot-detected", "children"),
        Output("bot-detection-rate", "children"), Output("bot-pro-bjp", "children"),
        Output("bot-anti-bjp", "children"), Output("bot-neutral", "children"),
        # 64-66: Bot charts
        Output("bot-inclination-pie", "figure"), Output("bot-sentiment-pie", "figure"),
        Output("bot-platform-bar", "figure"),
        # 67-68: Bot timeline + hashtags
        Output("bot-timeline", "figure"), Output("bot-hashtag-list", "children"),
        # 69: Key findings
        Output("bot-key-findings", "children"),
        # 70-76: Section insight summaries
        Output("insight-main-charts", "children"),
        Output("insight-adv-sentiment", "children"),
        Output("insight-social-media", "children"),
        Output("insight-popular-mentions", "children"),
        Output("insight-hashtags-alerts", "children"),
        Output("insight-influencers", "children"),
        Output("insight-political", "children"),
        # 77-82: Executive traffic light signals
        Output("exec-situation-signal", "style"),
        Output("exec-situation-text", "children"),
        Output("exec-mood-signal", "style"),
        Output("exec-mood-text", "children"),
        Output("exec-threat-signal", "style"),
        Output("exec-threat-text", "children"),
        # 83-88: KPI meaning labels
        Output("kpi-mood-meaning", "children"),
        Output("kpi-mentions-meaning", "children"),
        Output("kpi-positive-meaning", "children"),
        Output("kpi-negative-meaning", "children"),
        Output("kpi-bots-meaning", "children"),
        Output("kpi-favour-meaning", "children"),
        # 89-100: Regional Bengali Pulse (Section 10)
        Output("reg-bengali-mentions", "children"),       # 89
        Output("reg-bengali-positive", "children"),       # 90
        Output("reg-bengali-negative", "children"),       # 91
        Output("reg-bengali-reach", "children"),          # 92
        Output("reg-bengali-mentions-meaning", "children"),  # 93
        Output("reg-bengali-positive-meaning", "children"),  # 94
        Output("reg-bengali-hashtags", "children"),       # 95
        Output("reg-bengali-influencers", "children"),    # 96
        Output("reg-bengali-sentiment-pie", "figure"),    # 97
        Output("reg-bengali-topics-bar", "figure"),       # 98
        Output("reg-vs-national-bar", "figure"),          # 99
        Output("insight-regional-bengali", "children"),   # 100
        # 101-102: Trending topics + Live alerts (real-time)
        Output("trending-topics-list", "children"),       # 101
        Output("live-alerts-feed", "children"),           # 102
    ]

    @app.callback(outputs, [Input("refresh-interval", "n_intervals")])
    def update_dashboard(n):
        now_str = datetime.utcnow().strftime("%H:%M:%S UTC")
        kpi = _get_latest_kpi(kpi_store)
        dates = demo_dates(7)
        results = []

        # ── 0-5: KPI values ──
        results += [f"{kpi.rally_mood_score:.0f}", f"{kpi.mention_volume:,}",
                    f"{kpi.sentiment_share.positive:.1f}%", f"{kpi.sentiment_share.negative:.1f}%",
                    f"{kpi.bot_suspicion_score:.1f}%", f"{kpi.leader_favourability_score:.0f}"]

        # ── 6: Sentiment pie ──
        s = kpi.sentiment_share
        fig = go.Figure(go.Pie(labels=["Positive", "Negative", "Neutral", "Mixed"],
                               values=[s.positive, s.negative, s.neutral, s.mixed],
                               marker_colors=["#27AE60", "#E74C3C", "#95A5A6", "#F39C12"], hole=0.4))
        results.append(_fig_layout(fig, 250, showlegend=True))

        # ── 7: Emotion bar ──
        ed = kpi.emotion_distribution
        emos = {"Hope": ed.hope, "Anger": ed.anger, "Pride": ed.pride,
                "Trust": ed.trust, "Excitement": ed.excitement, "Fear": ed.fear}
        emos = {k: v for k, v in emos.items() if v > 0}
        fig = go.Figure(go.Bar(x=list(emos.values()), y=list(emos.keys()),
                               orientation="h", marker_color="#2980B9"))
        results.append(_fig_layout(fig, 250, margin=dict(t=20, b=20, l=80, r=20), xaxis_title="Score"))

        # ── 8: Platform bar ──
        plat = kpi.platform_breakdown
        fig = go.Figure(go.Bar(x=list(plat.keys()), y=list(plat.values()),
                               marker_color=[PLAT_COLORS.get(k, "#8E44AD") for k in plat]))
        results.append(_fig_layout(fig, 250, margin=dict(t=20, b=40, l=40, r=20), yaxis_title="Volume"))

        # ── 9: Hashtags ──
        ht_items = [html.Div([html.Span(f"#{h['hashtag']}", className="text-info"),
                              html.Span(f" ({h['count']})", className="text-muted")], className="mb-1")
                    for h in kpi.top_hashtags[:8]]
        results.append(ht_items or [html.P("No data", className="text-muted")])

        # ── 10: Influencers ──
        inf_items = [html.Div([html.Span(i.get("name", "?"), className="text-light"),
                               html.Span(f" — {i.get('engagement', 0):,}", className="text-muted small")], className="mb-1")
                     for i in kpi.top_influencers[:6]]
        results.append(inf_items or [html.P("No data", className="text-muted")])

        # ── 11: Alerts ──
        alerts = []
        if kpi.bot_suspicion_score > 20: alerts.append(html.Div("⚠️ Elevated bot activity", className="text-warning mb-1"))
        if s.negative > 40: alerts.append(html.Div("🔴 Negative sentiment > 40%", className="text-danger mb-1"))
        if kpi.polarization_index > 50: alerts.append(html.Div("⚠️ High polarization", className="text-warning mb-1"))
        if not alerts: alerts.append(html.Div("✅ No active alerts", className="text-success"))
        results.append(alerts)

        # ── 12-13: Clock + Phase ──
        results.append(now_str)
        results.append(dbc.Badge(kpi.phase.value.replace("_", " ").upper(),
                                 color="warning" if kpi.phase == RallyPhase.LIVE else "info"))

        # ── 14-15: Top 20 Influencer tables ──
        results.append(_build_inf_table(kpi.top_influencers_positive, "positive_pct", "success"))
        results.append(_build_inf_table(kpi.top_influencers_negative, "negative_pct", "danger"))

        # ── 16: Advanced Sentiment Pie ──
        adv = demo_advanced_sentiment()
        fig = go.Figure(go.Pie(labels=list(adv.keys()), values=list(adv.values()),
                               marker_colors=[ADV_COLORS[k] for k in adv], textinfo="label+percent",
                               textposition="outside", textfont=dict(size=14),
                               pull=[0.05 if k == "Admiration" else 0 for k in adv]))
        results.append(_fig_layout(fig, 480, margin=dict(t=50, b=50, l=50, r=50), showlegend=False))

        # ── 17: Polarity gauge ──
        pol = round(s.positive - s.negative, 1)
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=pol,
            number={"suffix": "%", "font": {"color": "white", "size": 36}},
            delta={"reference": 0, "increasing": {"color": "#27AE60"}, "decreasing": {"color": "#E74C3C"}},
            gauge={"axis": {"range": [-60, 60], "tickcolor": "white", "dtick": 20},
                   "bar": {"color": "#3498DB"}, "bgcolor": _BG,
                   "steps": [{"range": [-60, -20], "color": "rgba(231,76,60,0.3)"},
                             {"range": [-20, 20], "color": "rgba(149,165,166,0.2)"},
                             {"range": [20, 60], "color": "rgba(39,174,96,0.3)"}]},
            title={"text": "Net Polarity", "font": {"color": "white", "size": 16}}))
        results.append(_fig_layout(fig, 480, margin=dict(t=60, b=40, l=30, r=30)))

        # ── 18: Breakdown stats ──
        total_docs = s.total_docs or random.randint(1000, 3000)
        stats = [html.Div([html.Span("Total Docs: ", className="text-muted"),
                           html.Span(f"{total_docs:,}", className="text-info fw-bold")], className="mb-2")]
        for label, pct in adv.items():
            conf = round(random.uniform(0.72, 0.96), 2)
            stats.append(html.Div([
                html.Div([html.Span(f"{ADV_EMOJIS[label]} "), html.Span(label, style={"color": ADV_COLORS[label]}, className="fw-bold"),
                          html.Span(f" — {pct}%", className="text-light", style={"fontSize": "0.85rem"})]),
                html.Small(f"{int(total_docs * pct / 100):,} docs • conf: {conf:.0%}", className="text-muted"),
                dbc.Progress(value=pct, className="mb-0 mt-1", style={"height": "5px"}),
            ], className="mb-2 pb-1", style={"borderBottom": "1px solid #343a40", "fontSize": "0.85rem"}))
        results.append(stats)

        # ── 19: Sentiment timeline (with emotion breakdown like reference) ──
        pos_t = [round(random.uniform(35, 55), 1) for _ in range(7)]
        neg_t = [round(random.uniform(18, 35), 1) for _ in range(7)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=pos_t, name="Positive", mode="lines+markers",
                                 line=dict(color="#27AE60", width=3), fill="tozeroy", fillcolor="rgba(39,174,96,0.12)"))
        fig.add_trace(go.Scatter(x=dates, y=neg_t, name="Negative", mode="lines+markers",
                                 line=dict(color="#E74C3C", width=3), fill="tozeroy", fillcolor="rgba(231,76,60,0.12)"))
        for emo, color in [("Admiration", "#C8963E"), ("Neutral", "#8E8E8E"), ("Joy", "#D4D455"), ("Disgust", "#2A9D8F")]:
            fig.add_trace(go.Scatter(x=dates, y=[round(random.uniform(2, 40), 1) for _ in range(7)],
                                     name=emo, mode="lines", line=dict(color=color, width=2, dash="dot")))
        results.append(_fig_layout(fig, 300, margin=_MARGIN_MD, legend=dict(orientation="h", y=1.12),
                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                   yaxis=dict(gridcolor="rgba(255,255,255,0.08)")))

        # ── 20: Emotion radar ──
        labels = ["Hope", "Anger", "Pride", "Fear", "Trust", "Excitement"]
        vals = [ed.hope, ed.anger, ed.pride, ed.fear, ed.trust, ed.excitement]
        fig = go.Figure(go.Scatterpolar(r=vals + [vals[0]], theta=labels + [labels[0]], fill="toself",
                                         fillcolor="rgba(41,128,185,0.25)", line=dict(color="#3498DB", width=2)))
        results.append(_fig_layout(fig, 300, margin=dict(t=40, b=40, l=60, r=60), showlegend=False,
                                   polar=dict(bgcolor=_BG, radialaxis=dict(visible=True, color="white", gridcolor="rgba(255,255,255,0.1)"),
                                              angularaxis=dict(color="white"))))

        # ── 21-44: Social Media Stats (12 cards × value + delta) ──
        mv = kpi.mention_volume; reach = random.randint(300000, 800000)
        interactions = kpi.engagement_volume or random.randint(50000, 200000)
        likes = random.randint(40000, 80000); pos_c = int(mv * s.positive / 100)
        neg_c = int(mv * s.negative / 100); ugc = random.randint(400, 700)
        vids = random.randint(3, 12); ns_reach = random.randint(8000, 15000)
        ns_mentions = random.randint(1, 5); viral = random.randint(8, 35)
        avg_eng = round(interactions / max(mv, 1), 1)

        def _fk(v):
            if v >= 1e6: return f"{v/1e6:.1f}M"
            if v >= 1e3: return f"{v/1e3:.0f}K"
            return str(v)

        sm_vals = [(f"{mv:,}", f"+{mv:,} (+100%)"), (_fk(reach), f"+{_fk(reach)} (+100%)"),
                   (f"{interactions:,}", f"+{interactions:,} (+100%)"), (f"{likes:,}", f"+{likes:,} (+100%)"),
                   (f"{pos_c:,}", f"+{pos_c:,} (+100%)"), (f"{neg_c:,}", f"+{neg_c:,} (+100%)"),
                   (str(ugc), f"+{ugc} (+100%)"), (str(vids), f"+{vids} (+100%)"),
                   (_fk(ns_reach), f"+{_fk(ns_reach)} (+100%)"), (str(ns_mentions), f"+{ns_mentions} (+100%)"),
                   (str(viral), f"+{viral} (+100%)"), (str(avg_eng), f"+{avg_eng} (+100%)")]
        for val, delta in sm_vals:
            results.append(val); results.append(delta)

        # ── 45: Mentions timeline ──
        md = [random.randint(3, 20) for _ in range(3)] + [0] + [random.randint(80, 340) for _ in range(3)]
        fig = go.Figure(go.Scatter(x=dates, y=md, mode="lines+markers", line=dict(color="#3498DB", width=3),
                                   fill="tozeroy", fillcolor="rgba(52,152,219,0.12)"))
        results.append(_fig_layout(fig, 260, margin=_MARGIN_MD, showlegend=False,
                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict(gridcolor="rgba(255,255,255,0.08)")))

        # ── 46: Reach timeline ──
        rd = [random.randint(500, 2000) for _ in range(3)] + [random.randint(500, 1500)] + \
             [random.randint(150000, 2500000) for _ in range(2)] + [random.randint(40000, 70000)]
        fig = go.Figure(go.Scatter(x=dates, y=rd, mode="lines+markers", line=dict(color="#27AE60", width=3),
                                   fill="tozeroy", fillcolor="rgba(39,174,96,0.12)"))
        results.append(_fig_layout(fig, 260, margin=dict(t=20, b=40, l=60, r=20), showlegend=False,
                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict(gridcolor="rgba(255,255,255,0.08)")))

        # ── 47: Platform contribution (Overall Weightage) pie ──
        fig = go.Figure(go.Pie(labels=[k.title() for k in plat], values=list(plat.values()),
                               marker_colors=[PLAT_COLORS.get(k, "#8E44AD") for k in plat],
                               hole=0.45, textinfo="label+percent"))
        results.append(_fig_layout(fig, 260, showlegend=False))

        # ── 48: Engagement heatmap ──
        plist = list(plat.keys())
        z = [[max(0, int(plat[p] * random.uniform(0.01, 0.15))) for _ in range(3)] +
             [max(0, int(plat[p] * random.uniform(0, 0.05)))] +
             [int(plat[p] * random.uniform(0.6, 1.2)) for _ in range(3)] for p in plist]
        fig = go.Figure(go.Heatmap(z=z, x=dates, y=[p.title() for p in plist],
                                   colorscale=[[0, "rgba(0,0,0,0.8)"], [0.25, "#1a3a4a"],
                                               [0.5, "#2980B9"], [0.75, "#F39C12"], [1, "#E74C3C"]],
                                   showscale=True))
        results.append(_fig_layout(fig, 240, margin=dict(t=20, b=40, l=80, r=20)))

        # ── 49: Popular mentions grid ──
        mentions = demo_popular_mentions()
        cards = []
        src_colors = {"twitter.com": "#1DA1F2", "instagram.com": "#E1306C", "facebook.com": "#4267B2",
                      "youtube.com": "#FF0000", "ndtv.com": "#E53935", "news18.com": "#F39C12", "reddit.com": "#FF4500"}
        for i, m in enumerate(mentions, 1):
            cards.append(dbc.Card([
                dbc.CardBody([
                    html.Div([
                        dbc.Badge(str(i), color="success", className="me-2", style={"fontSize": "0.8rem"}),
                        html.Span(m["text"], className="text-light", style={"fontSize": "0.88rem"}),
                    ], className="mb-2"),
                    html.Div([html.Span(f" {t} ", className="text-success fw-bold me-1", style={"fontSize": "0.8rem"}) for t in m["hashtags"]]),
                    html.Div([
                        html.A(m["source"], style={"color": src_colors.get(m["source"], "#4FC3F7"), "fontSize": "0.75rem", "textDecoration": "none"}),
                        html.Span(f"  •  {m['date']}", className="text-muted", style={"fontSize": "0.72rem"}),
                        html.Span(f"  •  {m['engagement']:,} engagements", className="text-muted", style={"fontSize": "0.72rem"}),
                    ], className="mt-1"),
                ], style={"padding": "10px 14px"})
            ], className="bg-dark border-secondary mb-2", style={"borderLeft": "3px solid #27AE60"}))
        results.append(html.Div(cards))

        # ── 50: SM mentions table (Top 14) + trending hashtags merged ──
        _plat_icon_colors = {"X / Twitter": "#1DA1F2", "Facebook": "#4267B2", "Instagram": "#E1306C",
                              "YouTube": "#FF0000", "Reddit": "#FF4500", "News": "#F39C12"}
        sm_tbl = demo_sm_mentions_table()
        trend = demo_trending_hashtags()
        sm_rows = []
        for i, r in enumerate(sm_tbl, 1):
            plat_color = _plat_icon_colors.get(r[1], "#78909C")
            sm_rows.append(html.Tr([
                html.Td(str(i), style={"width": "30px", "textAlign": "center"}),
                html.Td(html.Span(r[0], className="text-light fw-bold")),
                html.Td(html.Span(r[1], style={"color": plat_color, "fontSize": "0.8rem", "fontWeight": "600"})),
                html.Td(f"{r[2]:,}", className="text-info"),
                html.Td(r[3], className="text-success", style={"textAlign": "right"}),
                html.Td(f"{r[4]:,}", style={"textAlign": "right"}),
                html.Td(html.Span(r[5], style={"color": "#66BB6A", "fontSize": "0.7rem", "fontWeight": "600"}),
                         style={"textAlign": "right"}),
            ], className="align-middle"))
        tbl1 = html.Div([
            html.Div([
                html.H6([
                    "📢 Top 14 Media Mentions ",
                    dbc.Badge("LIVE", color="success", className="ms-2",
                              style={"fontSize": "0.55rem", "animation": "pulse 2s infinite",
                                     "verticalAlign": "middle"}),
                ], className="text-info mb-0 px-3 pt-2 d-inline-flex align-items-center"),
                html.Small("Real-time across all social & digital platforms",
                           className="text-muted d-block px-3 mb-2", style={"fontSize": "0.7rem"}),
            ]),
            html.Table([
                html.Thead(html.Tr([html.Th("#"), html.Th("Profile"), html.Th("Platform"),
                                    html.Th("Followers"), html.Th("Voice Share", style={"textAlign": "right"}),
                                    html.Th("Influence", style={"textAlign": "right"}),
                                    html.Th("Updated", style={"textAlign": "right"})]), className="table-dark"),
                html.Tbody(sm_rows)
            ], className="table table-dark table-striped table-hover mb-0", style={"fontSize": "0.82rem"})
        ])
        tr_rows = []
        for i, r in enumerate(trend, 1):
            plat_color = _plat_icon_colors.get(r[1], "#78909C")
            tr_rows.append(html.Tr([
                html.Td(str(i), style={"width": "30px", "textAlign": "center"}),
                html.Td(html.Span(r[0], className="text-light fw-bold")),
                html.Td(html.Span(r[1], style={"color": plat_color, "fontSize": "0.8rem", "fontWeight": "600"})),
                html.Td(f"{r[2]:,}", style={"textAlign": "right"}),
                html.Td(str(r[3]), className="text-info", style={"textAlign": "right"}),
                html.Td(html.Span(r[4], style={"color": "#66BB6A", "fontSize": "0.7rem", "fontWeight": "600"}),
                         style={"textAlign": "right"}),
            ], className="align-middle"))
        tbl2 = html.Div([
            html.Div([
                html.H6([
                    "🔖 Trending Hashtag Profiles ",
                    dbc.Badge("LIVE", color="warning", className="ms-2",
                              style={"fontSize": "0.55rem", "verticalAlign": "middle"}),
                ], className="text-warning mb-0 px-3 pt-3 d-inline-flex align-items-center"),
                html.Small("Real-time tracking across X/Twitter, Facebook, Instagram, YouTube, Reddit",
                           className="text-muted d-block px-3 mb-2", style={"fontSize": "0.7rem"}),
            ]),
            html.Table([
                html.Thead(html.Tr([html.Th("#"), html.Th("Profile"), html.Th("Platform"),
                                    html.Th("Followers", style={"textAlign": "right"}),
                                    html.Th("Mentions", style={"textAlign": "right"}),
                                    html.Th("Updated", style={"textAlign": "right"})]), className="table-dark"),
                html.Tbody(tr_rows)
            ], className="table table-dark table-striped table-hover mb-0", style={"fontSize": "0.82rem"})
        ])
        results.append(html.Div([tbl1, tbl2]))

        # ── 51-52: Influencer pies (positive/negative voice share) ──
        for inf_list, color in [(kpi.top_influencers_positive[:5], "#27AE60"), (kpi.top_influencers_negative[:5], "#E74C3C")]:
            names = [i.get("name", "?") for i in inf_list]
            engs = [i.get("engagement", 0) for i in inf_list]
            total_eng = sum(engs)
            others = max(0, sum(i.get("engagement", 0) for i in (kpi.top_influencers_positive if color == "#27AE60" else kpi.top_influencers_negative)) - total_eng)
            labels = names + ["Others"]; vals = engs + [others]
            fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0,
                                   marker_colors=[color] * len(names) + ["#546E7A"],
                                   textinfo="label+percent", textposition="outside"))
            results.append(_fig_layout(fig, 300, margin=dict(t=30, b=30, l=30, r=30), showlegend=False))

        # ── 53-54: Political party pies ──
        for _ in range(2):
            raw = {"BJP": random.uniform(32, 45), "TMC": random.uniform(22, 35),
                   "LEFT": random.uniform(4, 10), "Congress": random.uniform(2, 7),
                   "Neutral": random.uniform(10, 20), "Others": random.uniform(2, 6)}
            total = sum(raw.values())
            raw = {k: round(v / total * 100, 1) for k, v in raw.items()}
            fig = go.Figure(go.Pie(labels=list(raw.keys()), values=list(raw.values()),
                                   marker_colors=[PARTY_COLORS[k] for k in raw], textinfo="label+percent",
                                   hole=0.4, pull=[0.05 if k == "BJP" else 0.03 if k == "TMC" else 0 for k in raw]))
            results.append(_fig_layout(fig, 320, showlegend=True, legend=dict(orientation="h", y=-0.1)))

        # ── 55: Influencer stance table ──
        results.append(_build_stance_table(demo_inf_stance(), has_volume=False))

        # ── 56: Hashtag stance table ──
        results.append(_build_stance_table(demo_ht_stance(), has_volume=True))

        # ── 57: Party sentiment bar ──
        parties = ["BJP", "TMC", "LEFT", "Congress", "Neutral"]
        pp = [round(random.uniform(40, 70), 1) for _ in parties]
        pn = [round(random.uniform(15, 45), 1) for _ in parties]
        pneu = [round(100 - a - b, 1) for a, b in zip(pp, pn)]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=parties, y=pp, name="Positive", marker_color="#27AE60", text=[f"{v}%" for v in pp], textposition="inside"))
        fig.add_trace(go.Bar(x=parties, y=pn, name="Negative", marker_color="#E74C3C", text=[f"{v}%" for v in pn], textposition="inside"))
        fig.add_trace(go.Bar(x=parties, y=pneu, name="Neutral", marker_color="#95A5A6", text=[f"{v}%" for v in pneu], textposition="inside"))
        results.append(_fig_layout(fig, 280, margin=_MARGIN_MD, barmode="group", legend=dict(orientation="h", y=1.1),
                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict(gridcolor="rgba(255,255,255,0.08)")))

        # ── 58-63: Bot Activity KPIs ──
        bot = demo_bot_activity()
        results += [
            f"{bot['total_accounts_analyzed']:,}",
            f"{bot['bot_accounts_detected']:,}",
            f"{bot['bot_percentage']:.1f}%",
            f"{bot['political_inclination']['Pro-BJP / PM Modi']:.1f}%",
            f"{bot['political_inclination']['Anti-BJP (Opposition)']:.1f}%",
            f"{bot['political_inclination']['Neutral / Undetermined']:.1f}%",
        ]

        # ── 64: Bot Inclination Pie ──
        incl = bot["political_inclination"]
        fig = go.Figure(go.Pie(
            labels=list(incl.keys()), values=list(incl.values()),
            marker_colors=["#FF6B00", "#00BCD4", "#78909C"],
            textinfo="label+percent", hole=0.45,
            pull=[0.05, 0.05, 0]))
        results.append(_fig_layout(fig, 300, showlegend=True, legend=dict(orientation="h", y=-0.15)))

        # ── 65: Bot Sentiment Pie ──
        bsent = bot["bot_sentiment"]
        fig = go.Figure(go.Pie(
            labels=list(bsent.keys()), values=list(bsent.values()),
            marker_colors=["#FF6B00", "#00BCD4", "#E53935", "#78909C"],
            textinfo="label+percent", hole=0.45))
        results.append(_fig_layout(fig, 300, showlegend=True, legend=dict(orientation="h", y=-0.15)))

        # ── 66: Bot Platform Bar ──
        bplat = bot["bot_platforms"]
        fig = go.Figure(go.Bar(
            x=list(bplat.keys()), y=list(bplat.values()),
            marker_color=["#1DA1F2", "#4267B2", "#E1306C", "#FF0000", "#78909C"],
            text=[f"{v}%" for v in bplat.values()], textposition="outside"))
        results.append(_fig_layout(fig, 300, margin=dict(t=30, b=40, l=40, r=20),
                                   yaxis_title="% of Bot Activity"))

        # ── 67: Bot Timeline ──
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=bot["bot_activity_timeline"],
            name="Bot Activity %", mode="lines+markers",
            line=dict(color="#FBBF24", width=3),
            fill="tozeroy", fillcolor="rgba(251,191,36,0.12)"))
        fig.add_hline(y=10, line_dash="dash", line_color="#F87171",
                      annotation_text="Alert Threshold (10%)", annotation_position="top right")
        results.append(_fig_layout(fig, 280, margin=_MARGIN_MD, showlegend=False,
                                   yaxis_title="Bot Activity %",
                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                   yaxis=dict(gridcolor="rgba(255,255,255,0.08)")))

        # ── 68: Bot Hashtag List ──
        incl_colors = {"Pro-BJP": "#FF6B00", "Pro-TMC": "#00BCD4", "Anti-BJP": "#E53935"}
        bot_ht_items = []
        for bh in bot["top_bot_hashtags"]:
            color = incl_colors.get(bh["inclination"], "#78909C")
            bot_ht_items.append(html.Div([
                html.Div([
                    html.Span(f"#{bh['hashtag']}", className="text-info fw-bold",
                              style={"fontSize": "0.85rem"}),
                    dbc.Badge(bh["inclination"],
                              style={"background": color, "marginLeft": "8px", "fontSize": "0.65rem"}),
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
                html.Div([
                    html.Span("Bot Penetration: ", className="text-muted", style={"fontSize": "0.75rem"}),
                    html.Span(f"{bh['bot_pct']}%", className="fw-bold",
                              style={"color": "#F87171" if bh["bot_pct"] > 20 else "#FBBF24" if bh["bot_pct"] > 12 else "#34D399",
                                     "fontSize": "0.85rem"}),
                ]),
                dbc.Progress(value=bh["bot_pct"], max=40,
                             color="danger" if bh["bot_pct"] > 20 else "warning" if bh["bot_pct"] > 12 else "success",
                             className="mb-0 mt-1", style={"height": "5px"}),
            ], className="mb-2 pb-2", style={"borderBottom": "1px solid #343a40"}))
        results.append(bot_ht_items)

        # ── 69: Key Findings ──
        icons = ["📊", "🟠", "🔵", "⚡", "🔗"]
        findings_items = []
        for i, finding in enumerate(bot["key_findings"]):
            findings_items.append(html.Div([
                html.Span(icons[i % len(icons)],
                          style={"fontSize": "1.1rem", "marginRight": "10px"}),
                html.Span(finding, style={"fontSize": "0.9rem", "color": "#E2E8F0", "lineHeight": "1.5"}),
            ], className="mb-2 pb-2",
               style={"borderBottom": "1px solid rgba(255,255,255,0.05)",
                       "display": "flex", "alignItems": "flex-start"}))
        results.append(findings_items)

        # ── 70-76: Section Insight Summaries ──────────────────────────
        def _insight(icon, lines):
            """Build a quick-read insight box with icon + summary bullets."""
            children = [html.Strong(f"{icon} Quick Read: ", style={"color": "#4FC3F7", "fontSize": "0.85rem"})]
            for i, line in enumerate(lines):
                if i > 0:
                    children.append(html.Span(" • ", style={"color": "#546E7A"}))
                children.append(html.Span(line, style={"fontSize": "0.82rem"}))
            return children

        # 70 — Main Charts (Sentiment + Emotion + Platform)
        dominant_sent = "Positive" if s.positive > s.negative else "Negative"
        top_emo = max(emos, key=emos.get) if emos else "Hope"
        top_plat = max(plat, key=plat.get).title()
        results.append(_insight("📊", [
            f"Overall mood is {dominant_sent.lower()} at {max(s.positive, s.negative):.0f}%",
            f"Dominant emotion is '{top_emo}' — reflects public temperament",
            f"{top_plat} leads platform activity with {max(plat.values()):,} mentions",
            f"Instagram contributing {plat.get('instagram', 0):,} mentions across rally discourse",
        ]))

        # 71 — Advanced Sentiment
        top_adv = max(adv, key=adv.get)
        results.append(_insight("🧠", [
            f"'{top_adv}' is the strongest advanced emotion at {adv[top_adv]:.1f}%",
            f"Net polarity stands at {pol:+.1f}% — {'positive tilt indicates favourable mood' if pol > 0 else 'negative tilt signals concern'}",
            f"Sentiment trend shows {'upward' if sum(pos_t[-3:]) > sum(pos_t[:3]) else 'declining'} positive momentum over last 7 days",
            f"Emotion radar highlights multi-dimensional public response beyond simple positive/negative",
        ]))

        # 72 — Social Media Summary
        results.append(_insight("📱", [
            f"{mv:,} total mentions with {_fk(reach)} social reach across all platforms",
            f"{pos_c:,} positive vs {neg_c:,} negative mentions — {pos_c/(pos_c+neg_c)*100:.0f}% positive ratio" if (pos_c + neg_c) > 0 else "Balanced sentiment across mentions",
            f"{viral} posts went viral with average engagement of {avg_eng} per mention",
            f"Instagram accounts for significant visual engagement share in rally coverage",
        ]))

        # 73 — Popular Mentions
        results.append(_insight("🔥", [
            f"Top 8 most-engaged posts collectively represent the most viral rally content",
            f"Twitter and Instagram dominate high-engagement mentions",
            f"Pro-rally hashtags (#ModiInKolkata, #BJP4Bengal) drive highest engagement",
            f"Opposition response posts are also gaining significant traction",
        ]))

        # 74 — Hashtags + Alerts
        top_ht = kpi.top_hashtags[0]["hashtag"] if kpi.top_hashtags else "N/A"
        alert_count = len([a for a in [kpi.bot_suspicion_score > 20, s.negative > 40, kpi.polarization_index > 50] if a])
        results.append(_insight("🏷️", [
            f"#{top_ht} is the most used hashtag with {kpi.top_hashtags[0]['count']:,} mentions" if kpi.top_hashtags else "No dominant hashtag detected",
            f"Top influencers driving discourse with {kpi.top_influencers[0].get('engagement', 0):,}+ engagements" if kpi.top_influencers else "Influencer data loading",
            f"{alert_count} active alert(s) detected" if alert_count > 0 else "No active alerts — rally discourse is within normal parameters",
        ]))

        # 75 — Influencers
        results.append(_insight("👥", [
            f"Top 20 positive influencers favour BJP/rally narrative with strong voice share",
            f"Top 20 negative influencers are primarily TMC-aligned and opposition media",
            f"Voice share distribution shows concentrated influence among top 5 accounts on each side",
            f"Cross-platform influence detected — key voices span Twitter, Facebook, and YouTube",
        ]))

        # 76 — Political Leaning
        results.append(_insight("🏛️", [
            f"BJP dominates influencer and hashtag alignment in rally discourse",
            f"TMC maintains strong counter-narrative through #KhelaHobe and allied voices",
            f"LEFT parties have a smaller but vocal digital footprint",
            f"Party-wise sentiment reveals BJP has higher positive ratio; opposition sentiment is more critical",
        ]))

        # ── 77-82: Executive Traffic Light Signals ────────────────────
        _light_base = {"width": "18px", "height": "18px", "borderRadius": "50%",
                       "display": "inline-block", "marginRight": "10px",
                       "verticalAlign": "middle"}

        def _traffic_color(score, thresholds=(60, 40)):
            """Return (color, glow) based on score. >60=green, 40-60=amber, <40=red."""
            if score >= thresholds[0]:
                return "#66BB6A", "0 0 12px rgba(102,187,106,0.6)"
            elif score >= thresholds[1]:
                return "#FFA726", "0 0 12px rgba(255,167,38,0.6)"
            else:
                return "#EF5350", "0 0 12px rgba(239,83,80,0.6)"

        # Overall Situation — composite score
        situation_score = (kpi.rally_mood_score * 0.3 +
                           s.positive * 0.3 +
                           (100 - kpi.bot_suspicion_score) * 0.2 +
                           (100 - kpi.polarization_index) * 0.2)
        sit_color, sit_glow = _traffic_color(situation_score)
        results.append({**_light_base, "background": sit_color, "boxShadow": sit_glow})
        if situation_score >= 60:
            results.append([html.Span("FAVOURABLE", style={"color": "#66BB6A"}),
                            html.Span(" — Rally sentiment is positive. Situation under control.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])
        elif situation_score >= 40:
            results.append([html.Span("MIXED", style={"color": "#FFA726"}),
                            html.Span(" — Sentiment is divided. Monitor closely for changes.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])
        else:
            results.append([html.Span("CONCERNING", style={"color": "#EF5350"}),
                            html.Span(" — Significant negative sentiment detected. Needs attention.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])

        # Public Mood
        mood_score = s.positive
        mood_color, mood_glow = _traffic_color(mood_score, (45, 30))
        results.append({**_light_base, "background": mood_color, "boxShadow": mood_glow})
        if mood_score >= 45:
            results.append([html.Span("POSITIVE", style={"color": "#66BB6A"}),
                            html.Span(f" — {mood_score:.0f}% of people are reacting positively to the rally.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])
        elif mood_score >= 30:
            results.append([html.Span("NEUTRAL-MIXED", style={"color": "#FFA726"}),
                            html.Span(f" — Only {mood_score:.0f}% positive. Public mood is lukewarm.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])
        else:
            results.append([html.Span("NEGATIVE", style={"color": "#EF5350"}),
                            html.Span(f" — Only {mood_score:.0f}% positive. Significant backlash detected.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])

        # Threat Level
        threat_score = (kpi.bot_suspicion_score * 0.4 + s.negative * 0.35 +
                        kpi.polarization_index * 0.25)
        threat_color, threat_glow = _traffic_color(100 - threat_score, (70, 50))
        results.append({**_light_base, "background": threat_color, "boxShadow": threat_glow})
        if threat_score < 30:
            results.append([html.Span("LOW RISK", style={"color": "#66BB6A"}),
                            html.Span(" — Minimal bot activity and opposition campaigns. Safe.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])
        elif threat_score < 50:
            results.append([html.Span("MODERATE RISK", style={"color": "#FFA726"}),
                            html.Span(f" — Bot activity at {kpi.bot_suspicion_score:.0f}%, negative sentiment at {s.negative:.0f}%.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])
        else:
            results.append([html.Span("HIGH RISK", style={"color": "#EF5350"}),
                            html.Span(f" — Elevated bot activity ({kpi.bot_suspicion_score:.0f}%) and opposition campaigns active.",
                                      style={"color": "#B0BEC5", "fontSize": "0.9rem"})])

        # ── 83-88: KPI Meaning Labels ─────────────────────────────────
        # Mood Score meaning
        ms = kpi.rally_mood_score
        if ms >= 65:
            results.append(html.Span("Excellent — strong public support", style={"color": "#66BB6A"}))
        elif ms >= 50:
            results.append(html.Span("Good — generally positive public mood", style={"color": "#81C784"}))
        elif ms >= 35:
            results.append(html.Span("Average — mixed public reactions", style={"color": "#FFA726"}))
        else:
            results.append(html.Span("Low — public mood is unfavourable", style={"color": "#EF5350"}))

        # Mentions meaning
        mv_val = kpi.mention_volume
        if mv_val >= 4000:
            results.append(html.Span("Very high buzz — rally is trending", style={"color": "#66BB6A"}))
        elif mv_val >= 2500:
            results.append(html.Span("Good buzz — people are discussing", style={"color": "#81C784"}))
        else:
            results.append(html.Span("Moderate — could be higher", style={"color": "#FFA726"}))

        # Positive % meaning
        if s.positive >= 50:
            results.append(html.Span("Strong — majority is supportive", style={"color": "#66BB6A"}))
        elif s.positive >= 35:
            results.append(html.Span("Decent — more positive than negative", style={"color": "#81C784"}))
        else:
            results.append(html.Span("Weak — positive sentiment is low", style={"color": "#FFA726"}))

        # Negative % meaning
        if s.negative >= 40:
            results.append(html.Span("⚠️ High — significant opposition noise", style={"color": "#EF5350"}))
        elif s.negative >= 25:
            results.append(html.Span("Moderate — some criticism present", style={"color": "#FFA726"}))
        else:
            results.append(html.Span("Low — minimal negative reactions", style={"color": "#66BB6A"}))

        # Bot % meaning
        bs = kpi.bot_suspicion_score
        if bs >= 20:
            results.append(html.Span("⚠️ High — fake accounts very active", style={"color": "#EF5350"}))
        elif bs >= 10:
            results.append(html.Span("Moderate — some fake activity detected", style={"color": "#FFA726"}))
        else:
            results.append(html.Span("Low — mostly genuine accounts", style={"color": "#66BB6A"}))

        # Leader favourability meaning
        lf = kpi.leader_favourability_score
        if lf >= 60:
            results.append(html.Span("Strong — leader is viewed very positively", style={"color": "#66BB6A"}))
        elif lf >= 45:
            results.append(html.Span("Good — generally favourable view", style={"color": "#81C784"}))
        else:
            results.append(html.Span("Needs work — perception could improve", style={"color": "#FFA726"}))

        # ── 89-100: Regional Bengali Pulse ──────────────────────────────
        reg = demo_regional_bengali()

        # 89-92: KPI values
        results.append(f"{reg['total_mentions']:,}")
        results.append(f"{reg['positive_pct']:.1f}%")
        results.append(f"{reg['negative_pct']:.1f}%")
        results.append(f"{reg['reach']:,}")

        # 93: Bengali mentions meaning
        if reg["total_mentions"] >= 3500:
            results.append(html.Span("Very active — Bengali discourse is high", style={"color": "#66BB6A"}))
        elif reg["total_mentions"] >= 2500:
            results.append(html.Span("Active — decent regional engagement", style={"color": "#81C784"}))
        else:
            results.append(html.Span("Moderate — regional buzz could be higher", style={"color": "#FFA726"}))

        # 94: Bengali positive meaning
        if reg["positive_pct"] >= 48:
            results.append(html.Span("Strong regional support detected", style={"color": "#66BB6A"}))
        elif reg["positive_pct"] >= 38:
            results.append(html.Span("Decent — more positive than negative", style={"color": "#81C784"}))
        else:
            results.append(html.Span("Mixed — regional sentiment is divided", style={"color": "#FFA726"}))

        # 95: Bengali Hashtags card body
        ht_items = []
        for bh in sorted(reg["hashtags"], key=lambda x: x["count"], reverse=True):
            color = BENGALI_HASHTAG_COLORS.get(bh["party"], "#78909C")
            ht_items.append(html.Div([
                html.Div([
                    html.Span(bh["tag"], className="fw-bold", style={"fontSize": "1rem", "color": "#E2E8F0"}),
                    html.Span(f"  ({bh['en']})", className="text-muted", style={"fontSize": "0.78rem"}),
                    dbc.Badge(bh["party"], style={"background": color, "marginLeft": "8px", "fontSize": "0.65rem"}),
                ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"}),
                html.Div([
                    html.Span(f"{bh['count']:,} mentions", className="text-info", style={"fontSize": "0.8rem"}),
                ], className="mt-1"),
                dbc.Progress(value=min(bh["count"] / 25, 100), className="mb-0 mt-1", style={"height": "4px"},
                             color="warning" if bh["party"] == "Pro-BJP" else "info" if bh["party"] == "Pro-TMC" else "success"),
            ], className="mb-2 pb-2", style={"borderBottom": "1px solid #343a40"}))
        results.append(ht_items)

        # 96: Bengali Influencers table
        stance_colors = {"Pro-BJP": "#FF6B00", "Pro-TMC": "#00BCD4", "Pro-LEFT": "#E53935",
                         "Neutral": "#78909C", "Regional": "#52B788"}
        inf_rows = []
        for i, inf in enumerate(sorted(reg["influencers"], key=lambda x: x["engagement"], reverse=True), 1):
            sc = stance_colors.get(inf["stance"], "#78909C")
            inf_rows.append(html.Tr([
                html.Td(str(i), style={"width": "30px", "textAlign": "center"}),
                html.Td([html.Span(inf["handle"], className="text-info fw-bold"),
                          html.Br(),
                          html.Small(inf["name"], className="text-muted")]),
                html.Td(inf["platform"], className="text-muted", style={"fontSize": "0.8rem"}),
                html.Td(f"{inf['followers']:,}", style={"textAlign": "right", "fontSize": "0.82rem"}),
                html.Td(f"{inf['engagement']:,}", className="text-light", style={"textAlign": "right"}),
                html.Td(dbc.Badge(inf["stance"], style={"background": sc, "fontSize": "0.65rem"})),
            ], className="align-middle"))
        inf_table = html.Table([
            html.Thead(html.Tr([html.Th("#"), html.Th("Handle / Name"), html.Th("Platform"),
                                html.Th("Followers", style={"textAlign": "right"}),
                                html.Th("Engagement", style={"textAlign": "right"}),
                                html.Th("Stance")]), className="table-dark"),
            html.Tbody(inf_rows)
        ], className="table table-dark table-striped table-hover mb-0", style={"fontSize": "0.82rem"})
        results.append(inf_table)

        # 97: Bengali sentiment pie
        fig = go.Figure(go.Pie(
            labels=["ইতিবাচক (Positive)", "নেতিবাচক (Negative)", "নিরপেক্ষ (Neutral)"],
            values=[reg["positive_pct"], reg["negative_pct"], reg["neutral_pct"]],
            marker_colors=["#27AE60", "#E74C3C", "#95A5A6"], hole=0.45,
            textinfo="label+percent", textfont=dict(size=11)))
        results.append(_fig_layout(fig, 300, margin=dict(t=20, b=30, l=20, r=20), showlegend=True,
                                   legend=dict(orientation="h", y=-0.15, font=dict(size=10))))

        # 98: Bengali topics bar
        topics = reg["sentiment_by_topic"]
        topic_names = list(topics.keys())
        topic_pos = [topics[t]["pos"] for t in topic_names]
        topic_neg = [topics[t]["neg"] for t in topic_names]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=topic_names, y=topic_pos, name="Positive", marker_color="#27AE60",
                             text=[f"{v}%" for v in topic_pos], textposition="inside"))
        fig.add_trace(go.Bar(x=topic_names, y=topic_neg, name="Negative", marker_color="#E74C3C",
                             text=[f"{v}%" for v in topic_neg], textposition="inside"))
        results.append(_fig_layout(fig, 300, margin=dict(t=20, b=60, l=40, r=20), barmode="group",
                                   legend=dict(orientation="h", y=1.1),
                                   xaxis=dict(tickangle=-25, gridcolor="rgba(255,255,255,0.05)"),
                                   yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="%")))

        # 99: Regional vs National comparison bar
        rvn = reg["regional_vs_national"]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["Regional Bengali", "National"], y=[rvn["regional_positive"], rvn["national_positive"]],
                             name="Positive", marker_color="#27AE60",
                             text=[f"{rvn['regional_positive']}%", f"{rvn['national_positive']}%"], textposition="inside"))
        fig.add_trace(go.Bar(x=["Regional Bengali", "National"], y=[rvn["regional_negative"], rvn["national_negative"]],
                             name="Negative", marker_color="#E74C3C",
                             text=[f"{rvn['regional_negative']}%", f"{rvn['national_negative']}%"], textposition="inside"))
        results.append(_fig_layout(fig, 280, margin=dict(t=20, b=40, l=40, r=20), barmode="group",
                                   legend=dict(orientation="h", y=1.1),
                                   xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                                   yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="%")))

        # 100: Regional Bengali insight
        results.append(_insight("🏛️", [
            reg["key_insight"],
            f"Top Bengali hashtag is {reg['hashtags'][0]['tag']} with {reg['hashtags'][0]['count']:,} mentions",
            f"Regional positive sentiment at {reg['positive_pct']:.0f}% vs {rvn['national_positive']:.0f}% nationally",
            f"Bengali influencers driving {reg['reach']:,} total reach across platforms",
        ]))

        # ── 101: Trending Topics (real-time) ────────────────────────────
        topics_data = demo_trending_topics()
        topic_items = []
        sent_colors = {"Mostly Positive": "#27AE60", "Positive": "#27AE60", "Mixed": "#FFA726",
                       "Negative": "#EF5350", "Negative (Anti-BJP)": "#EF5350",
                       "Neutral-Positive": "#81C784", "Polarized": "#F39C12"}
        for t in topics_data:
            sc = sent_colors.get(t["sentiment"], "#78909C")
            topic_items.append(html.Div([
                html.Div([
                    html.Span(t["trend"], style={"fontSize": "1.1rem", "marginRight": "8px"}),
                    html.Span(t["topic"], className="text-light fw-bold",
                              style={"fontSize": "0.92rem"}),
                    dbc.Badge(t["change"],
                              color="success" if t["trend"] == "🔺" else "danger" if t["trend"] == "🔻" else "secondary",
                              className="ms-2", style={"fontSize": "0.6rem"}),
                    html.Span(f" • {t['updated']}", style={"color": "#66BB6A",
                              "fontSize": "0.68rem", "marginLeft": "8px", "fontWeight": "600"}),
                ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "2px"}),
                html.Div([
                    html.Span(f"{t['volume']:,} mentions", className="text-info",
                              style={"fontSize": "0.78rem", "marginRight": "12px"}),
                    html.Span(t["sentiment"], style={"color": sc, "fontSize": "0.75rem",
                              "fontWeight": "600", "marginRight": "12px"}),
                    html.Span(" • ".join(t["platforms"]),
                              style={"color": "#78909C", "fontSize": "0.7rem"}),
                ], className="mt-1"),
            ], className="mb-2 pb-2", style={"borderBottom": "1px solid #343a40"}))
        results.append(topic_items)

        # ── 102: Live Alerts Feed (real-time) ───────────────────────────
        alerts_data = demo_live_alerts()
        level_styles = {
            "critical": {"borderLeft": "4px solid #EF5350", "background": "rgba(239,83,80,0.06)"},
            "warning": {"borderLeft": "4px solid #FFA726", "background": "rgba(255,167,38,0.04)"},
            "info": {"borderLeft": "4px solid #4FC3F7", "background": "rgba(79,195,247,0.04)"},
        }
        alert_items = []
        for a in sorted(alerts_data, key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x["level"], 3)):
            style = {**level_styles.get(a["level"], {}),
                     "padding": "10px 14px", "borderRadius": "8px", "marginBottom": "8px"}
            alert_items.append(html.Div([
                html.Div([
                    html.Span(a["icon"], style={"fontSize": "1rem", "marginRight": "8px"}),
                    html.Span(a["msg"], style={"color": "#E2E8F0", "fontSize": "0.82rem",
                              "lineHeight": "1.4"}),
                ], style={"display": "flex", "alignItems": "flex-start"}),
                html.Div([
                    dbc.Badge(a["platform"], className="me-2",
                              style={"fontSize": "0.6rem", "background": "#37474F"}),
                    html.Span(a["time"], style={"color": "#66BB6A", "fontSize": "0.68rem",
                              "fontWeight": "600"}),
                ], className="mt-1 ms-4"),
            ], style=style))
        results.append(alert_items)

        expected = len(outputs)
        actual = len(results)
        if actual != expected:
            logger.error(f"Output mismatch: got {actual}, expected {expected}")
            # Pad or trim to match
            if actual < expected:
                empty_fig = __import__('plotly.graph_objects', fromlist=['graph_objects']).Figure()
                empty_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                for i in range(actual, expected):
                    o = outputs[i]
                    if o.component_property == "figure":
                        results.append(empty_fig)
                    elif o.component_property == "style":
                        results.append({})
                    else:
                        results.append("—")
            else:
                results = results[:expected]

        return tuple(results)

    return app


# ─── Helpers ──────────────────────────────────────────────────────────

def _build_inf_table(inf_list, pct_key, color):
    from dash import html
    import dash_bootstrap_components as dbc
    rows = []
    for i, inf in enumerate(inf_list[:20], 1):
        pct = inf.get(pct_key, 0)
        rows.append(html.Tr([
            html.Td(str(i), style={"width": "35px", "textAlign": "center"}),
            html.Td([html.Span(inf.get("name", "?"), className="text-light fw-bold"), html.Br(),
                     html.Small(inf.get("platform", ""), className="text-muted")]),
            html.Td(f"{inf.get('followers', 0):,}", className="text-muted", style={"textAlign": "right"}),
            html.Td(f"{inf.get('engagement', 0):,}", className="text-info", style={"textAlign": "right"}),
            html.Td(dbc.Progress(value=pct, color=color, className="mb-0", style={"height": "16px", "minWidth": "70px"},
                                 label=f"{pct:.0f}%"), style={"width": "120px"}),
        ], className="align-middle"))
    return html.Table([
        html.Thead(html.Tr([html.Th("#", style={"width": "35px"}), html.Th("Influencer"),
                            html.Th("Followers", style={"textAlign": "right"}),
                            html.Th("Engagement", style={"textAlign": "right"}),
                            html.Th(pct_key.replace("_", " ").title(), style={"width": "120px"})]), className="table-dark"),
        html.Tbody(rows)
    ], className="table table-dark table-striped table-hover mb-0", style={"fontSize": "0.85rem"}) if rows else html.P("No data", className="text-muted p-3")


def _build_stance_table(data, has_volume=False):
    from dash import html
    import dash_bootstrap_components as dbc
    from engine.dashboard.demo_data import PARTY_BADGE
    _plat_colors = {"X / Twitter": "#1DA1F2", "Facebook": "#4267B2", "Instagram": "#E1306C",
                    "YouTube": "#FF0000", "Reddit": "#FF4500", "News": "#F39C12",
                    "News, X / Twitter": "#F39C12", "All Platforms": "#66BB6A",
                    "X / Twitter, Facebook": "#1DA1F2", "X / Twitter, Instagram": "#1DA1F2",
                    "X / Twitter, YouTube": "#1DA1F2", "X / Twitter, Facebook, Instagram": "#1DA1F2",
                    "Facebook, Instagram": "#4267B2", "Instagram, YouTube": "#E1306C",
                    "X / Twitter, Reddit": "#1DA1F2", "Facebook, X / Twitter": "#4267B2",
                    "Reddit, X / Twitter": "#FF4500", "News, X / Twitter, YouTube": "#F39C12"}
    rows = []
    for i, entry in enumerate(data, 1):
        if has_volume:
            name, party, stance, volume, conf, platforms, updated = entry
        else:
            name, party, stance, conf, platforms, updated = entry
            volume = None
        plat_color = _plat_colors.get(platforms, "#78909C")
        cells = [
            html.Td(str(i), style={"width": "30px", "textAlign": "center"}),
            html.Td(html.Span(name, className="text-info fw-bold" if has_volume else "text-light fw-bold")),
            html.Td(dbc.Badge(party, color=PARTY_BADGE.get(party, "secondary"), className="px-2")),
            html.Td(stance, className="text-muted", style={"fontSize": "0.82rem"}),
            html.Td(html.Span(platforms, style={"color": plat_color, "fontSize": "0.72rem"})),
        ]
        if has_volume:
            cells.append(html.Td(f"{volume:,}", className="text-light", style={"textAlign": "right"}))
        cells.append(html.Td(dbc.Progress(value=conf * 100, color="success" if conf > 0.8 else "warning" if conf > 0.6 else "secondary",
                                          className="mb-0", style={"height": "12px", "minWidth": "50px"}, label=f"{conf:.0%}"),
                             style={"width": "90px"}))
        cells.append(html.Td(html.Span(updated, style={"color": "#66BB6A", "fontSize": "0.68rem", "fontWeight": "600"}),
                             style={"textAlign": "right", "whiteSpace": "nowrap"}))
        rows.append(html.Tr(cells, className="align-middle"))

    hdrs = [html.Th("#"), html.Th("Hashtag" if has_volume else "Influencer"), html.Th("Party"),
            html.Th("Stance"), html.Th("Platforms")]
    if has_volume: hdrs.append(html.Th("Volume", style={"textAlign": "right"}))
    hdrs.append(html.Th("Conf.", style={"width": "90px"}))
    hdrs.append(html.Th("Updated", style={"textAlign": "right"}))

    return html.Table([html.Thead(html.Tr(hdrs), className="table-dark"), html.Tbody(rows)],
                      className="table table-dark table-striped table-hover mb-0", style={"fontSize": "0.8rem"})


def _get_latest_kpi(store=None):
    if store and len(store) > 0:
        return store[-1]
    from engine.models import EmotionDistribution
    return KPISnapshot(
        campaign_id="demo", phase=RallyPhase.PRE_24H,
        window_start=datetime.utcnow(), window_end=datetime.utcnow(),
        mention_volume=random.randint(1500, 5000), engagement_volume=random.randint(50000, 200000),
        sentiment_share=SentimentShare(positive=round(random.uniform(35, 55), 1), negative=round(random.uniform(20, 35), 1),
                                       neutral=round(random.uniform(15, 25), 1), mixed=round(random.uniform(5, 15), 1),
                                       total_docs=random.randint(1000, 3000)),
        rally_mood_score=round(random.uniform(45, 75), 1), leader_favourability_score=round(random.uniform(40, 70), 1),
        share_of_voice=round(random.uniform(30, 60), 1), bot_suspicion_score=round(random.uniform(5, 25), 1),
        polarization_index=round(random.uniform(20, 55), 1),
        platform_breakdown={"twitter": random.randint(500, 2000), "facebook": random.randint(300, 1000),
                            "instagram": random.randint(400, 1200), "youtube": random.randint(100, 500),
                            "news": random.randint(50, 200), "reddit": random.randint(20, 100)},
        emotion_distribution=EmotionDistribution(hope=round(random.uniform(10, 30), 1), anger=round(random.uniform(10, 25), 1),
                                                  pride=round(random.uniform(5, 15), 1), excitement=round(random.uniform(10, 25), 1),
                                                  trust=round(random.uniform(5, 20), 1), fear=round(random.uniform(3, 10), 1)),
        top_hashtags=[{"hashtag": h, "count": random.randint(50, 800)} for h in
                      ["ModiInKolkata", "KhelaHobe", "BJP4Bengal", "BengalElection2026", "ModiMegaRally"]],
        top_influencers=[{"name": n, "engagement": random.randint(1000, 20000)} for n in
                         ["@BJPBengal", "@AITCofficial", "@ndtv", "@ABPAnanda"]],
        top_influencers_positive=[
            {"name": n, "platform": p, "followers": f, "engagement": random.randint(e[0], e[1]), "positive_pct": round(random.uniform(pp[0], pp[1]), 1)}
            for n, p, f, e, pp in [
                ("@BJPBengal", "Twitter", 285000, (15000, 30000), (78, 95)), ("@NaMo_BJP", "Twitter", 520000, (12000, 28000), (75, 92)),
                ("Suvendu Adhikari", "Facebook", 410000, (10000, 22000), (72, 90)), ("@BJP4India", "Twitter", 1850000, (9000, 20000), (70, 88)),
                ("Amit Shah Fan", "Facebook", 320000, (8000, 18000), (68, 87)), ("@DilipGhoshBJP", "Twitter", 175000, (7000, 16000), (66, 85)),
                ("Bengal BJP Youth", "Instagram", 98000, (6000, 15000), (65, 84)), ("@ABPAnanda", "Twitter", 450000, (5500, 14000), (63, 82)),
                ("India Today Bn", "YouTube", 680000, (5000, 13000), (62, 80)), ("@SushmitaDev", "Twitter", 145000, (4500, 12000), (60, 79)),
                ("Modi Supporters WB", "Facebook", 210000, (4000, 11000), (58, 78)), ("@TimesNowBn", "Twitter", 380000, (3800, 10000), (57, 76)),
                ("BengalRisingBJP", "Instagram", 67000, (3500, 9500), (55, 75)), ("@News18Bengali", "Twitter", 290000, (3200, 9000), (54, 74)),
                ("Kolkata BJP Ward", "Facebook", 45000, (3000, 8500), (53, 73)), ("@RepublicBangla", "Twitter", 220000, (2800, 8000), (52, 72)),
                ("NaMo Brigade", "YouTube", 89000, (2600, 7500), (51, 71)), ("@ZeeBangla24", "Twitter", 310000, (2400, 7000), (50, 70)),
                ("BJP Mahila WB", "Facebook", 52000, (2200, 6500), (49, 69)), ("@Dev_Adhikari_", "Twitter", 125000, (2000, 6000), (48, 68)),
            ]],
        top_influencers_negative=[
            {"name": n, "platform": p, "followers": f, "engagement": random.randint(e[0], e[1]), "negative_pct": round(random.uniform(np[0], np[1]), 1)}
            for n, p, f, e, np in [
                ("@AITCofficial", "Twitter", 560000, (15000, 30000), (75, 92)), ("@MamataOfficial", "Twitter", 890000, (12000, 28000), (72, 90)),
                ("TMC Youth", "Facebook", 320000, (10000, 22000), (70, 88)), ("@AbhishekBan", "Twitter", 210000, (9000, 20000), (68, 86)),
                ("Bengal AntiNRC", "Facebook", 185000, (8000, 18000), (66, 85)), ("@SaugataRoyMP", "Twitter", 130000, (7000, 16000), (64, 83)),
                ("No BJP Bengal", "Instagram", 75000, (6000, 15000), (62, 82)), ("@ABOROY_TMC", "Twitter", 95000, (5500, 14000), (60, 80)),
                ("Student Fed WB", "Facebook", 110000, (5000, 13000), (58, 79)), ("@CPIMBengal", "Twitter", 88000, (4500, 12000), (57, 78)),
                ("Bengal Farmer", "YouTube", 62000, (4000, 11000), (55, 76)), ("@DidiKeBolo", "Twitter", 150000, (3800, 10000), (54, 75)),
                ("Kolkata Protests", "Facebook", 48000, (3500, 9500), (52, 74)), ("@TheWireBangla", "Twitter", 290000, (3200, 9000), (51, 73)),
                ("Civil Society BN", "Facebook", 35000, (3000, 8500), (50, 72)), ("@ScrollBengal", "Twitter", 180000, (2800, 8000), (49, 71)),
                ("Anti-Rally KOL", "Instagram", 28000, (2600, 7500), (48, 70)), ("@QuintBengali", "Twitter", 220000, (2400, 7000), (47, 69)),
                ("Workers Union", "Facebook", 42000, (2200, 6500), (46, 68)), ("@NewsClickBn", "Twitter", 98000, (2000, 6000), (45, 67)),
            ]],
    )


def run_server(port=8050, debug=False):
    app = create_app()
    if app:
        logger.info(f"Dashboard starting on http://localhost:{port}")
        app.run(host="0.0.0.0", port=port, debug=debug)
    else:
        logger.error("Cannot start dashboard — Dash not available")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8050)))
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    run_server(port=args.port, debug=args.debug)
