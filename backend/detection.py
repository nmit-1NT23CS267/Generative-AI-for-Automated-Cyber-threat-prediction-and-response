import json
import re
from collections import Counter
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


def make_alert(category, severity, confidence, reason, response, line):
    return {
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "reason": reason,
        "recommended_response": response,
        "log": line
    }


def detect_alerts():
    lines = read_logs()
    alerts = []

    failed_logins = Counter()
    download_counts = Counter()

    for line in lines:
        lower_line = line.lower()

        if "login" in lower_line and "failed" in lower_line:
            email_or_user = line.split("|")[2].strip()
            failed_logins[email_or_user] += 1

        if "download" in lower_line:
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 3:
                ip_or_user = parts[2]
                download_counts[ip_or_user] += 1

        if SQLI_PATTERN.search(line):
            alerts.append(
                make_alert(
                    "SQL Injection",
                    "Critical",
                    0.98,
                    "Suspicious SQL injection pattern found in input or log.",
                    "Reject input and use parameterized database queries.",
                    line
                )
            )

        if XSS_PATTERN.search(line):
            alerts.append(
                make_alert(
                    "Cross-Site Scripting",
                    "High",
                    0.96,
                    "Suspicious script or event-handler pattern found.",
                    "Reject or sanitize input and alert the administrator.",
                    line
                )
            )

        if "/admin" in lower_line and ("403" in lower_line or "unknown" in lower_line):
            alerts.append(
                make_alert(
                    "Unauthorized Access",
                    "High",
                    0.94,
                    "Unknown user attempted to access a restricted endpoint.",
                    "Deny access and temporarily restrict the source.",
                    line
                )
            )

    for user, count in failed_logins.items():
        if count >= 3:
            alerts.append(
                make_alert(
                    "Brute Force",
                    "High",
                    0.92,
                    f"{count} failed login attempts detected for the same user.",
                    "Temporarily restrict login and alert the administrator.",
                    user
                )
            )

    for user_or_ip, count in download_counts.items():
        if count >= 3:
            alerts.append(
                make_alert(
                    "Bot Activity",
                    "High",
                    0.90,
                    f"{count} resume downloads detected for the same user or IP.",
                    "Apply throttling and temporarily restrict access.",
                    user_or_ip
                )
            )

    ALERT_FILE.write_text(
        json.dumps(alerts, indent=4),
        encoding="utf-8"
    )

    return alerts