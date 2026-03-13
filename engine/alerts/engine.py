"""
JanPulse AI — Alert System
Real-time alert monitoring with multi-channel delivery (Slack, Email, SMS).
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from engine.models import Alert, AlertSeverity, KPISnapshot


class AlertRule:
    """A single alert rule with threshold and cooldown."""

    def __init__(self, name: str, metric_name: str, condition: str,
                 threshold: float, severity: AlertSeverity,
                 channels: list[str] = None, cooldown_minutes: int = 15):
        self.name = name
        self.metric_name = metric_name
        self.condition = condition  # "gt" | "lt" | "delta_gt" | "delta_lt"
        self.threshold = threshold
        self.severity = severity
        self.channels = channels or ["slack"]
        self.cooldown_minutes = cooldown_minutes
        self._last_fired: Optional[datetime] = None

    def evaluate(self, current_value: float, previous_value: float = None) -> Optional[Alert]:
        """Evaluate rule against current value. Returns Alert if triggered."""
        now = datetime.utcnow()

        # Cooldown check
        if self._last_fired and (now - self._last_fired).total_seconds() < self.cooldown_minutes * 60:
            return None

        triggered = False
        if self.condition == "gt" and current_value > self.threshold:
            triggered = True
        elif self.condition == "lt" and current_value < self.threshold:
            triggered = True
        elif self.condition == "delta_gt" and previous_value is not None:
            delta = current_value - previous_value
            if delta > self.threshold:
                triggered = True
        elif self.condition == "delta_lt" and previous_value is not None:
            delta = current_value - previous_value
            if delta < -self.threshold:
                triggered = True

        if triggered:
            self._last_fired = now
            return Alert(
                alert_type=self.name,
                severity=self.severity,
                message=f"[{self.severity.value.upper()}] {self.name}: {self.metric_name}={current_value:.1f} "
                        f"(threshold: {self.condition} {self.threshold})",
                metric_name=self.metric_name,
                metric_value=current_value,
                threshold=self.threshold,
            )
        return None


# ─── DEFAULT ALERT RULES ─────────────────────────────────────────────────

DEFAULT_RULES = [
    AlertRule("Mood Drop Alert", "rally_mood_score", "delta_lt", 15,
             AlertSeverity.CRITICAL, ["slack", "sms", "email"], 15),
    AlertRule("Negative Sentiment Surge", "negative_sentiment_pct", "gt", 60,
             AlertSeverity.HIGH, ["slack", "email"], 15),
    AlertRule("Bot Attack Alert", "bot_suspicion_score", "gt", 40,
             AlertSeverity.HIGH, ["slack", "email"], 20),
    AlertRule("Misinformation Burst", "misinformation_count_10min", "gt", 50,
             AlertSeverity.CRITICAL, ["slack", "sms", "email"], 30),
    AlertRule("Volume Spike", "mention_volume_5min", "delta_gt", 500,
             AlertSeverity.MEDIUM, ["slack"], 10),
    AlertRule("Viral Moment", "clip_share_rate", "gt", 100,
             AlertSeverity.INFO, ["slack"], 5),
    AlertRule("High Polarization", "polarization_index", "gt", 70,
             AlertSeverity.HIGH, ["slack", "email"], 30),
    AlertRule("Low Mood Warning", "rally_mood_score", "lt", 30,
             AlertSeverity.HIGH, ["slack", "email"], 20),
]


class AlertEngine:
    """Monitors KPIs against rules and dispatches alerts."""

    def __init__(self, rules: list[AlertRule] = None, campaign_id: str = ""):
        self.rules = rules or DEFAULT_RULES
        self.campaign_id = campaign_id
        self.alert_history: list[Alert] = []
        self._previous_kpi: Optional[KPISnapshot] = None

    def evaluate(self, kpi: KPISnapshot) -> list[Alert]:
        """Evaluate all rules against current KPI snapshot."""
        alerts = []

        # Map metric names to KPI values
        metric_values = {
            "rally_mood_score": kpi.rally_mood_score,
            "negative_sentiment_pct": kpi.sentiment_share.negative,
            "positive_sentiment_pct": kpi.sentiment_share.positive,
            "bot_suspicion_score": kpi.bot_suspicion_score,
            "polarization_index": kpi.polarization_index,
            "mention_volume": kpi.mention_volume,
            "leader_favourability": kpi.leader_favourability_score,
            "share_of_voice": kpi.share_of_voice,
            "opposition_intensity": kpi.opposition_counter_intensity,
            "misinformation_count_10min": kpi.misinformation_flag_count,
        }

        previous_values = {}
        if self._previous_kpi:
            previous_values = {
                "rally_mood_score": self._previous_kpi.rally_mood_score,
                "mention_volume_5min": self._previous_kpi.mention_volume,
                "negative_sentiment_pct": self._previous_kpi.sentiment_share.negative,
            }

        for rule in self.rules:
            current_val = metric_values.get(rule.metric_name)
            if current_val is None:
                continue
            prev_val = previous_values.get(rule.metric_name)

            alert = rule.evaluate(current_val, prev_val)
            if alert:
                alert.campaign_id = self.campaign_id
                alerts.append(alert)
                self.alert_history.append(alert)
                logger.warning(f"ALERT: {alert.message}")

        self._previous_kpi = kpi
        return alerts

    def dispatch(self, alerts: list[Alert]):
        """Send alerts through configured channels."""
        for alert in alerts:
            for rule in self.rules:
                if rule.name == alert.alert_type:
                    for channel in rule.channels:
                        try:
                            if channel == "slack":
                                self._send_slack(alert)
                            elif channel == "email":
                                self._send_email(alert)
                            elif channel == "sms":
                                self._send_sms(alert)
                        except Exception as e:
                            logger.error(f"Alert dispatch error ({channel}): {e}")

    def _send_slack(self, alert: Alert):
        """Send alert to Slack channel."""
        token = os.getenv("SLACK_BOT_TOKEN", "")
        channel = os.getenv("SLACK_CHANNEL", "#alerts")
        if not token:
            logger.debug(f"Slack alert (no token): {alert.message}")
            return

        try:
            from slack_sdk import WebClient
            client = WebClient(token=token)
            severity_emoji = {
                AlertSeverity.CRITICAL: ":rotating_light:",
                AlertSeverity.HIGH: ":warning:",
                AlertSeverity.MEDIUM: ":large_yellow_circle:",
                AlertSeverity.INFO: ":information_source:",
            }
            emoji = severity_emoji.get(alert.severity, ":bell:")
            client.chat_postMessage(
                channel=channel,
                text=f"{emoji} *{alert.alert_type}*\n{alert.message}\n"
                     f"_Metric: {alert.metric_name} = {alert.metric_value:.1f} | "
                     f"Threshold: {alert.threshold} | {alert.timestamp.strftime('%H:%M:%S UTC')}_"
            )
            logger.info(f"Slack alert sent: {alert.alert_type}")
        except Exception as e:
            logger.error(f"Slack send error: {e}")

    def _send_email(self, alert: Alert):
        """Send alert via email."""
        import smtplib
        from email.mime.text import MIMEText

        smtp_host = os.getenv("ALERT_EMAIL_SMTP_HOST", "")
        if not smtp_host:
            logger.debug(f"Email alert (no SMTP): {alert.message}")
            return

        try:
            msg = MIMEText(
                f"Rally Intelligence Alert\n\n"
                f"Type: {alert.alert_type}\n"
                f"Severity: {alert.severity.value}\n"
                f"Message: {alert.message}\n"
                f"Metric: {alert.metric_name} = {alert.metric_value:.1f}\n"
                f"Threshold: {alert.threshold}\n"
                f"Time: {alert.timestamp.isoformat()}\n"
                f"Campaign: {alert.campaign_id}"
            )
            msg["Subject"] = f"[JanPulse {alert.severity.value.upper()}] {alert.alert_type}"
            msg["From"] = os.getenv("ALERT_EMAIL_FROM", "")
            msg["To"] = os.getenv("ALERT_EMAIL_TO", "")

            with smtplib.SMTP(smtp_host, int(os.getenv("ALERT_EMAIL_SMTP_PORT", 587))) as server:
                server.starttls()
                server.login(msg["From"], os.getenv("ALERT_EMAIL_PASSWORD", ""))
                server.send_message(msg)
            logger.info(f"Email alert sent: {alert.alert_type}")
        except Exception as e:
            logger.error(f"Email send error: {e}")

    def _send_sms(self, alert: Alert):
        """Send alert via SMS (Twilio)."""
        sid = os.getenv("TWILIO_SID", "")
        if not sid:
            logger.debug(f"SMS alert (no Twilio): {alert.message}")
            return

        try:
            from twilio.rest import Client
            client = Client(sid, os.getenv("TWILIO_AUTH_TOKEN", ""))
            client.messages.create(
                body=f"JanPulse ALERT [{alert.severity.value}]: {alert.alert_type} - "
                     f"{alert.metric_name}={alert.metric_value:.1f}",
                from_=os.getenv("TWILIO_FROM_NUMBER", ""),
                to=os.getenv("ALERT_SMS_TO", "")
            )
            logger.info(f"SMS alert sent: {alert.alert_type}")
        except Exception as e:
            logger.error(f"SMS send error: {e}")
