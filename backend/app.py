import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from recruitment import router as recruitment_router
from auth import router as auth_router
from email_alerts import EmailAlertSender
from file_scanner import FileScanner
from ml_detection import ThreatMLDetector
from explainer import explain_threat, explain_all_alerts
from datetime import datetime
from database import get_db_connection

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import requests

from detection import detect_alerts

app = FastAPI(
    title="Cyber Recruitment Security API",
    description="API for detecting cyber threats in a recruitment platform",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(recruitment_router, prefix="/api/recruitment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
LOG_DIR = BASE_DIR / "logs"

LOG_FILE = LOG_DIR / "activity.log"
ALERT_FILE = LOG_DIR / "alerts.json"

UPLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx"
}

MAX_FILE_SIZE = 5 * 1024 * 1024

# Initialize ML detector
ml_detector = ThreatMLDetector()

# Initialize file scanner
file_scanner = FileScanner()

# Initialize email alert sender
email_sender = EmailAlertSender()


def write_log(message: str):
    """
    Writes a log to the file and to the database.
    """
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(message + "\n")

    write_log_to_db(message)


def write_log_to_db(message: str):
    """
    Parses the log message and stores it in PostgreSQL.
    """
    try:
        parts = [part.strip() for part in message.split("|")]

        if len(parts) < 5:
            return

        timestamp_str = parts[0]
        event_type = parts[1]
        email = parts[2]
        ip_address = parts[3]
        status = parts[4]
        details = parts[5] if len(parts) > 5 else ""

        timestamp = datetime.fromisoformat(timestamp_str)

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_logs
                (timestamp, event_type, email, ip_address, status, details)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (timestamp, event_type, email, ip_address, status, details)
            )
    except Exception as error:
        print(f"Database log error: {error}")


def get_client_ip(request: Request):
    """
    Gets the IP address of the client making the request.
    """
    if request.client:
        return request.client.host

    return "unknown"


@app.get("/")
def home():
    """
    Checks whether the API is running.
    """
    return {
        "message": "Cyber Recruitment Security API is running"
    }


@app.get("/health")
def health_check():
    """
    Checks the health status of the API.
    """
    return {
        "status": "healthy",
        "service": "cyber recruitment security api"
    }


@app.post("/register-user")
def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    company: str = Form(""),
    role_title: str = Form(""),
    experience: str = Form(""),
    skills: str = Form(""),
    team: str = Form("")
):
    """Create a role-based user entry in the database."""
    role = (role or "").strip().lower()
    if role not in {"candidate", "recruiter", "tester"}:
        return {"status": "error", "message": "Invalid role"}

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM user_accounts WHERE LOWER(email)=LOWER(%s) AND role=%s",
                    (email, role)
                )
                if cur.fetchone():
                    return {"status": "exists", "message": "User already exists for this role"}

                cur.execute(
                    """
                    INSERT INTO user_accounts
                    (role, name, email, password, company, role_title, experience, skills, team, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (role, name, email, password, company, role_title, experience, skills, team, datetime.now(), None)
                )
                conn.commit()
    except Exception as error:
        return {"status": "error", "message": str(error)}

    return {"status": "success", "message": "User registered successfully"}


@app.post("/login-user")
def login_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    """Authenticate a role-based user against the database."""
    role = (role or "").strip().lower()
    if role not in {"candidate", "recruiter", "tester"}:
        return {"status": "error", "message": "Invalid role"}

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, role, name, email, password, company, role_title, experience, skills, team, created_at, last_login
                    FROM user_accounts
                    WHERE LOWER(email)=LOWER(%s) AND role=%s AND password=%s
                    """,
                    (email, role, password)
                )
                row = cur.fetchone()

        if not row:
            return {"status": "error", "message": "Invalid credentials for this role"}

        user = {
            "id": row[0],
            "role": row[1],
            "name": row[2],
            "email": row[3],
            "company": row[5],
            "role_title": row[6],
            "experience": row[7],
            "skills": row[8],
            "team": row[9],
            "created_at": str(row[10]),
            "last_login": str(row[11]) if row[11] else None
        }

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_accounts SET last_login=%s WHERE id=%s",
                    (datetime.now(), row[0])
                )
                conn.commit()

        return {"status": "success", "message": "Login successful", "user": user}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@app.get("/users-by-role")
def get_users_by_role(role: str = ""):
    """List all users for a selected role."""
    role = (role or "").strip().lower()
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if role:
                    cur.execute(
                        """
                        SELECT id, role, name, email, company, role_title, experience, skills, team, created_at, last_login
                        FROM user_accounts
                        WHERE role=%s
                        ORDER BY created_at DESC
                        """,
                        (role,)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, role, name, email, company, role_title, experience, skills, team, created_at, last_login
                        FROM user_accounts
                        ORDER BY created_at DESC
                        """
                    )
                rows = cur.fetchall()

        users = [{
            "id": row[0],
            "role": row[1],
            "name": row[2],
            "email": row[3],
            "company": row[4],
            "role_title": row[5],
            "experience": row[6],
            "skills": row[7],
            "team": row[8],
            "created_at": str(row[9]),
            "last_login": str(row[10]) if row[10] else None
        } for row in rows]

        return {"status": "success", "users": users}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@app.post("/submit-application")
def submit_application(
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    resume_file_name: str = Form(...),
    resume_data: str = Form(...),
    malicious_flag: bool = Form(False),
    status: str = Form("Submitted")
):
    """Stores a candidate application and resume data."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO candidate_applications
                    (candidate_name, candidate_email, job_title, company, resume_file_name, resume_data, applied_at, malicious_flag, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (candidate_name, candidate_email, job_title, company, resume_file_name, resume_data, datetime.now(), malicious_flag, status)
                )
                conn.commit()
    except Exception as error:
        return {"status": "error", "message": str(error)}

    return {"status": "success", "message": "Application submitted successfully"}


@app.get("/applications")
def get_applications(email: str = ""):
    """Return candidate applications, optionally filtered by email."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if email:
                    cur.execute(
                        """
                        SELECT id, candidate_name, candidate_email, job_title, company, resume_file_name, resume_data, applied_at, malicious_flag, status
                        FROM candidate_applications
                        WHERE LOWER(candidate_email)=LOWER(%s)
                        ORDER BY applied_at DESC
                        """,
                        (email,)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, candidate_name, candidate_email, job_title, company, resume_file_name, resume_data, applied_at, malicious_flag, status
                        FROM candidate_applications
                        ORDER BY applied_at DESC
                        """
                    )
                rows = cur.fetchall()

        applications = [{
            "id": row[0],
            "candidate_name": row[1],
            "candidate_email": row[2],
            "job_title": row[3],
            "company": row[4],
            "resume_file_name": row[5],
            "resume_data": row[6],
            "applied_at": str(row[7]),
            "malicious_flag": bool(row[8]),
            "status": row[9]
        } for row in rows]

        return {"status": "success", "applications": applications}
    except Exception as error:
        return {"status": "error", "message": str(error)}


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Demo login endpoint.

    For this academic prototype, the password 123456
    represents a successful login.
    """

    ip_address = get_client_ip(request)

    if password == "123456":
        status = "success"
        message = "Login successful"
    else:
        status = "failed"
        message = "Login failed"

    log_line = (
        f"{datetime.now().isoformat(timespec='seconds')} | "
        f"login | "
        f"{email} | "
        f"{ip_address} | "
        f"{status}"
    )

    write_log(log_line)

    return {
        "email": email,
        "status": status,
        "message": message
    }


@app.post("/upload-resume")
async def upload_resume(
    request: Request,
    email: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Uploads a resume after checking its extension and size.
    """

    original_filename = file.filename or ""
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "status": "rejected",
            "reason": "Only PDF, DOC, and DOCX files are allowed."
        }

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        return {
            "status": "rejected",
            "reason": "File size must be less than 5 MB."
        }

    safe_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / safe_filename

    file_path.write_bytes(file_content)

    # Scan file for malicious content
    scan_result = file_scanner.scan_file(file_path, original_filename)

    ip_address = get_client_ip(request)

    if not scan_result["is_safe"]:
        # File is malicious - delete it
        file_path.unlink()
        
        # Log security alert
        log_line = (
            f"{datetime.now().isoformat(timespec='seconds')} | "
            f"malicious_upload | "
            f"{email} | "
            f"{ip_address} | "
            f"{original_filename} | "
            f"blocked"
        )
        write_log(log_line)
        
        # Store alert in database
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    alert_id = f"MAL{uuid.uuid4().hex[:6]}"
                    cur.execute("""
                        INSERT INTO alerts (alert_id, category, severity, risk_score, confidence, reason, recommended_response, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (alert_id, "Malicious File", "Critical", 95, 0.95, 
                          f"Malicious content detected: {', '.join(scan_result['threats'])}", 
                          "Block user and investigate", datetime.now()))
                    conn.commit()
            
            # Send email alert for critical threats
            if scan_result["threats"]:
                alert_data = {
                    "alert_id": alert_id,
                    "category": "Malicious File",
                    "severity": "Critical",
                    "risk_score": 95,
                    "reason": f"Malicious content detected: {', '.join(scan_result['threats'])}",
                    "recommended_response": "Block user and investigate",
                    "timestamp": datetime.now()
                }
            email_sender.send_alert_email(alert_data)
                    
        except Exception as e:
            print(f"Alert error: {e}")
        
        return {
            "status": "rejected",
            "reason": "File contains suspicious content",
            "threats": scan_result["threats"]
        }

    # File is safe
    log_line = (
        f"{datetime.now().isoformat(timespec='seconds')} | "
        f"resume_upload | "
        f"{email} | "
        f"{ip_address} | "
        f"{safe_filename} | "
        f"success"
    )

    write_log(log_line)

    return {
        "status": "success",
        "message": "Resume uploaded successfully",
        "stored_filename": safe_filename,
        "scan_details": scan_result["file_type"]
    }

@app.get("/logs")
def get_logs():
    """
    Returns all collected activity logs.
    """

    if not LOG_FILE.exists():
        return {
            "logs": []
        }

    logs = LOG_FILE.read_text(
        encoding="utf-8"
    ).splitlines()

    return {
        "total_logs": len(logs),
        "logs": logs
    }


@app.post("/analyze")
def analyze_logs():
    """
    Analyzes activity logs and generates security alerts.
    """

    alerts = detect_alerts()

    return {
        "message": "Log analysis completed",
        "alert_count": len(alerts),
        "alerts": alerts
    }


@app.get("/alerts")
def get_alerts():
    """
    Returns generated security alerts.
    """

    if not ALERT_FILE.exists():
        return []

    alert_text = ALERT_FILE.read_text(
        encoding="utf-8"
    )

    if not alert_text.strip():
        return []

    return json.loads(alert_text)

@app.get("/db-logs")
def get_db_logs():
    """
    Returns activity logs from the PostgreSQL database.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, timestamp, event_type, email, ip_address, status, details
                    FROM activity_logs
                    ORDER BY timestamp DESC
                    LIMIT 50
                    """
                )

                rows = cur.fetchall()

        logs = [
            {
                "id": row[0],
                "timestamp": str(row[1]),
                "event_type": row[2],
                "email": row[3],
                "ip_address": row[4],
                "status": row[5],
                "details": row[6]
            }
            for row in rows
        ]

        return {
            "total_logs": len(logs),
            "logs": logs
        }
    except Exception as error:
        return {
            "error": str(error),
            "message": "Database connection failed"
        }

@app.get("/db-alerts")
def get_db_alerts():
    """
    Returns alerts from the PostgreSQL database.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT alert_id, timestamp, category, severity, risk_score, confidence, reason, recommended_response
                    FROM alerts
                    ORDER BY timestamp DESC
                    LIMIT 50
                    """
                )

                rows = cur.fetchall()

        alerts = [
            {
                "alert_id": row[0],
                "timestamp": str(row[1]),
                "category": row[2],
                "severity": row[3],
                "risk_score": row[4],
                "confidence": float(row[5]) if row[5] else 0,
                "reason": row[6],
                "recommended_response": row[7]
            }
            for row in rows
        ]

        return {
            "total_alerts": len(alerts),
            "alerts": alerts
        }
    except Exception as error:
        return {
            "error": str(error),
            "message": "Database connection failed"
        }

@app.get("/explain-threats")
def explain_threats():
    """
    Generates human-readable explanations for all detected threats.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT alert_id, timestamp, category, severity, risk_score, confidence, reason, recommended_response
                    FROM alerts
                    ORDER BY timestamp DESC
                    LIMIT 50
                    """
                )

                rows = cur.fetchall()

        alerts = [
            {
                "alert_id": row[0],
                "timestamp": str(row[1]),
                "category": row[2],
                "severity": row[3],
                "risk_score": row[4],
                "confidence": float(row[5]) if row[5] else 0,
                "reason": row[6],
                "recommended_response": row[7]
            }
            for row in rows
        ]

        explanations = explain_all_alerts(alerts)

        return {
            "total_explanations": len(explanations),
            "explanations": explanations
        }
    except Exception as error:
        return {
            "error": str(error),
            "message": "Explanation generation failed"
        }

@app.get("/simulate-attack")
def simulate_attack(attack_type: str = "brute_force"):
    """Simulates various cyber attacks for testing"""
    import random
    import string
    
    attack_types = ["brute_force", "sql_injection", "bot_activity", "ddos"]
    selected_attack = attack_type if attack_type in attack_types else random.choice(attack_types)
    
    alert_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    timestamp = datetime.now()
    
    # Generate attack-specific data
    if selected_attack == "brute_force":
        category = "Brute Force"
        severity = "High"
        description = "Multiple failed login attempts detected"
        risk_score = 75
    elif selected_attack == "sql_injection":
        category = "SQL Injection"
        severity = "Critical"
        description = "SQL injection pattern detected in input"
        risk_score = 95
    elif selected_attack == "bot_activity":
        category = "Bot Activity"
        severity = "High"
        description = "Automated bot behavior detected"
        risk_score = 70
    elif selected_attack == "ddos":
        category = "DDoS"
        severity = "Critical"
        description = "Distributed denial of service attack detected"
        risk_score = 90
    else:
        category = "Unknown"
        severity = "Medium"
        description = "Suspicious activity detected"
        risk_score = 50
    
    # Store alert in database
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
    INSERT INTO alerts (alert_id, category, severity, risk_score, confidence, reason, recommended_response, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (alert_id, category, severity, risk_score, 0.9, f"Simulated {selected_attack} attack", f"Block {selected_attack} attempts", timestamp))
                conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
    
    # ML-based anomaly detection
    try:
        is_anomaly, confidence, score = ml_detector.predict(
            user_id="simulated_user",
            timestamp=timestamp,
            ip="192.168.1.100",
            user_agent="Attack-Simulator/1.0"
        )
        
        if is_anomaly and confidence > 0.5:
            ml_alert_id = f"ML{alert_id}"
            ml_alert = {
                "alert_id": ml_alert_id,
                "category": "ML Anomaly",
                "severity": "High" if confidence > 0.7 else "Medium",
                "description": f"ML-detected anomalous behavior (confidence: {confidence:.2f})",
                "source_ip": "192.168.1.100",
                "timestamp": timestamp,
                "risk_score": int(confidence * 100)
            }
            
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
    INSERT INTO alerts (alert_id, category, severity, risk_score, confidence, reason, recommended_response, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (ml_alert_id, ml_alert["category"], ml_alert["severity"], 
      ml_alert["risk_score"], 0.85, ml_alert["description"], 
      "Investigate anomalous behavior", ml_alert["timestamp"]))
                    conn.commit()
    except Exception as e:
        print(f"ML detection error: {e}")
    
    return {
        "status": "success",
        "message": f"{selected_attack} attack simulation completed",
        "alert_id": alert_id,
        "category": category,
        "severity": severity
    }

@app.get("/test-ml")
def test_ml_prediction():
    """Test ML prediction directly"""
    try:
        is_anomaly, confidence, score = ml_detector.predict(
            user_id="test_user",
            timestamp=datetime.now(),
            ip="192.168.1.100",
            user_agent="Test-Agent/1.0"
        )
        
        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "score": score,
            "message": "Anomaly detected" if is_anomaly else "Normal behavior"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-email")
def test_email():
    """Send test email to verify configuration"""
    success = email_sender.send_test_email()
    
    if success:
        return {"status": "success", "message": "Test email sent successfully"}
    else:
        return {"status": "error", "message": "Failed to send test email. Check configuration."}

@app.post("/train-ml")
def train_ml_model():
    """Train ML model on historical login data"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT email, timestamp, ip_address, details
                    FROM activity_logs 
                    WHERE event_type = 'login'
                    ORDER BY timestamp DESC
                    LIMIT 100
                    """
                )
                rows = cur.fetchall()
        
        historical_data = []
        for row in rows:
            historical_data.append({
                "user_id": row[0],
                "timestamp": row[1],
                "ip_address": row[2],
                "user_agent": row[3] if row[3] else ""
            })
        
        if ml_detector.train(historical_data):
            return {"status": "success", "message": "ML model trained successfully"}
        else:
            return {"status": "warning", "message": "Insufficient data for training"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
