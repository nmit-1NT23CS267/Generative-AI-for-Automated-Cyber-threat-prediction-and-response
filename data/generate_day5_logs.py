from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "backend" / "logs"
LOG_FILE = LOG_DIR / "activity.log"

LOG_DIR.mkdir(exist_ok=True)


def write_log(line):
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Normal event
write_log(
    f"{timestamp} | login | normal_user@mail.com | "
    f"192.168.1.10 | success"
)

# Three failed logins for brute-force detection
for _ in range(3):
    write_log(
        f"{timestamp} | login | brute_user@mail.com | "
        f"10.0.0.5 | failed"
    )

# SQL injection-like test input
write_log(
    f"{timestamp} | input | test_user@mail.com | "
    f"10.0.0.6 | failed | ' OR 1=1 --"
)

# XSS-like test input
write_log(
    f"{timestamp} | input | test_user@mail.com | "
    f"10.0.0.7 | failed | <script>alert(1)</script>"
)

# Repeated resume downloads for bot detection
for _ in range(3):
    write_log(
        f"{timestamp} | resume_download | bot_user@mail.com | "
        f"9.9.9.9 | success"
    )

# Unauthorized admin access
write_log(
    f"{timestamp} | api | unknown | 10.10.10.10 | "
    f"/admin | 403"
)

print("Day 5 synthetic test logs were added.")
