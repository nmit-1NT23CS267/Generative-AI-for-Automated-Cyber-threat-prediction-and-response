import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "activity.log"
ALERT_FILE = BASE_DIR / "logs" / "alerts.json"

SQLI_PATTERN = re.compile(
    r"(\bor\b\s+\d+\s*=\s*\d+|union\s+select|drop\s+table|"
    r"insert\s+into|delete\s+from|--|%27)",
    re.IGNORECASE
)

XSS_PATTERN = re.compile(
    r"(<script|</script>|javascript:|onerror\s*=|onload\s*=)",
    re.IGNORECASE
)


def read_logs():
    if not LOG_FILE.exists():
        return []

    return LOG_FILE.read_text(encoding="utf-8").splitlines()


def calculate_risk_score(severity):
    scores = {
        "Low": 25,
        "Medium": 50,
        "High": 75,
        "Critical": 95
    }
    return scores.get(severity, 0)


def create_alert(category, severity, confidence, reason, response, log_line):
    alert_key = f"{category}|{log_line}"
    alert_id = hashlib.sha256(
        alert_key.encode("utf-8")
    ).hexdigest()[:12]

    return {
        "alert_id": alert_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "severity": severity,
        "risk_score": calculate_risk_score(severity),
        "confidence": confidence,
        "reason": reason,
        "recommended_response": response,
        "log": log_line
    }


def detect_alerts():
    lines = read_logs()
    raw_alerts = []

    failed_logins = Counter()
    download_counts = Counter()

    for line in lines:
        lower_line = line.lower()

        if "login" in lower_line and "failed" in lower_line:
            parts = [part.strip() for part in line.split("|")]

            if len(parts) >= 3:
                user = parts[2]
                failed_logins[user] += 1

        if "download" in lower_line:
            parts = [part.strip() for part in line.split("|")]

            if len(parts) >= 3:
                user_or_ip = parts[2]
                download_counts[user_or_ip] += 1

        if SQLI_PATTERN.search(line):
            raw_alerts.append(
                create_alert(
                    "SQL Injection",
                    "Critical",
                    0.98,
                    "A suspicious SQL injection pattern was found.",
                    "Reject the input and use parameterized database queries.",
                    line
                )
            )

        if XSS_PATTERN.search(line):
            raw_alerts.append(
                create_alert(
                    "Cross-Site Scripting",
                    "High",
                    0.96,
                    "A suspicious script or event-handler pattern was found.",
                    "Reject or sanitize the input and alert the administrator.",
                    line
                )
            )

        if (
            "/admin" in lower_line
            and ("403" in lower_line or "unknown" in lower_line)
        ):
            raw_alerts.append(
                create_alert(
                    "Unauthorized Access",
                    "High",
                    0.94,
                    "An unknown user attempted to access a restricted endpoint.",
                    "Deny access and temporarily restrict the source.",
                    line
                )
            )

    for user, count in failed_logins.items():
        if count >= 3:
            raw_alerts.append(
                create_alert(
                    "Brute Force",
                    "High",
                    0.92,
                    f"{count} failed login attempts were detected.",
                    "Temporarily restrict login and alert the administrator.",
                    user
                )
            )

    for user_or_ip, count in download_counts.items():
        if count >= 3:
            raw_alerts.append(
                create_alert(
                    "Bot Activity",
                    "High",
                    0.90,
                    f"{count} resume downloads were detected.",
                    "Apply throttling and temporarily restrict access.",
                    user_or_ip
                )
            )

    unique_alerts = {}
    for alert in raw_alerts:
        unique_alerts[alert["alert_id"]] = alert

    alerts = list(unique_alerts.values())

    ALERT_FILE.write_text(
        json.dumps(alerts, indent=4),
        encoding="utf-8"
    )

    store_alerts(alerts)

    return alerts


def store_alerts(alerts):
    """
    Stores alerts in PostgreSQL.
    """
    try:
        from database import get_db_connection

        with get_db_connection() as conn:
            for alert in alerts:
                conn.execute(
                    """
                    INSERT INTO alerts
                    (alert_id, timestamp, category, severity, risk_score, confidence, reason, recommended_response, log_entry)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        alert.get("alert_id"),
                        datetime.fromisoformat(alert.get("timestamp")),
                        alert.get("category"),
                        alert.get("severity"),
                        alert.get("risk_score"),
                        float(alert.get("confidence")),
                        alert.get("reason"),
                        alert.get("recommended_response"),
                        alert.get("log")
                    )
                )
    except Exception as error:
        print(f"Alert storage error: {error}")
