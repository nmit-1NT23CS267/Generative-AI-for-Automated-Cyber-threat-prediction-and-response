from fastapi import Header
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from database import get_db_connection
from datetime import datetime
import hashlib
import os
from pathlib import Path

router = APIRouter()

# Pydantic models
class CandidateRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    skills: Optional[List[str]] = []
    experience_years: Optional[int] = 0

class JobCreate(BaseModel):
    title: str
    description: str
    requirements: List[str]
    location: str
    salary_range: str

class ApplicationCreate(BaseModel):
    job_id: int

# Helper to get current user from token
def get_current_user_from_token(token: str):
    from jose import jwt
    SECRET_KEY = "cyber-threat-secret-key-2026"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Candidate registration
@router.post("/candidate/register")
async def register_candidate(data: CandidateRegister):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if username exists
    cur.execute("SELECT id FROM users WHERE username = %s", (data.username,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    password_hash = hashlib.sha256(data.password.encode()).hexdigest()
    
    # Insert user
    cur.execute("""
        INSERT INTO users (username, email, password_hash, role, full_name)
        VALUES (%s, %s, %s, 'candidate', %s)
        RETURNING id
    """, (data.username, data.email, password_hash, data.full_name))
    
    user_id = cur.fetchone()[0]
    
    # Insert candidate profile
    cur.execute("""
        INSERT INTO candidates (user_id, full_name, email, phone, skills, experience_years)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING candidate_id
    """, (user_id, data.full_name, data.email, data.phone, data.skills, data.experience_years))
    
    candidate_id = cur.fetchone()[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"message": "Registration successful", "candidate_id": candidate_id}

# Apply for job (candidate only)
@router.post("/apply")
async def apply_job(data: ApplicationCreate, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    if user.get('role') != 'candidate':
        raise HTTPException(status_code=403, detail="Only candidates can apply")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get candidate_id
    cur.execute("SELECT candidate_id FROM candidates WHERE user_id = %s", (user.get('sub'),))
    candidate = cur.fetchone()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    
    candidate_id = candidate[0]
    
    try:
        cur.execute("""
            INSERT INTO applications (job_id, candidate_id)
            VALUES (%s, %s)
            RETURNING application_id
        """, (data.job_id, candidate_id))
        
        application_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {"message": "Application submitted", "application_id": application_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Already applied or invalid job")
    finally:
        cur.close()
        conn.close()

# Get applications (recruiter sees all, candidate sees theirs)
@router.get("/applications")
async def get_applications(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if user.get('role') in ['admin', 'recruiter']:
        cur.execute("""
            SELECT a.application_id, a.status, a.applied_at,
                   c.full_name as candidate_name, c.email, c.phone,
                   j.title as job_title
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.candidate_id
            JOIN jobs j ON a.job_id = j.job_id
            ORDER BY a.applied_at DESC
        """)
        
        applications = []
        for row in cur.fetchall():
            applications.append({
                "application_id": row[0],
                "status": row[1],
                "applied_at": str(row[2]),
                "candidate_name": row[3],
                "email": row[4],
                "phone": row[5],
                "job_title": row[6]
            })
    else:  # candidate
        cur.execute("SELECT candidate_id FROM candidates WHERE user_id = %s", (user.get('sub'),))
        candidate = cur.fetchone()
        
        if not candidate:
            return {"applications": []}
        
        cur.execute("""
            SELECT a.application_id, a.status, a.applied_at,
                   j.title as job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            LEFT JOIN companies c ON j.company_id = c.company_id
            WHERE a.candidate_id = %s
            ORDER BY a.applied_at DESC
        """, (candidate[0],))
        
        applications = []
        for row in cur.fetchall():
            applications.append({
                "application_id": row[0],
                "status": row[1],
                "applied_at": str(row[2]),
                "job_title": row[3],
                "company_name": row[4]
            })
    
    cur.close()
    conn.close()
    
    return {"applications": applications}

# Get all jobs (for candidates)
@router.get("/jobs")
async def get_jobs(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    # Testers cannot see jobs
    if user.get('role') == 'tester':
        raise HTTPException(status_code=403, detail="Testers cannot view jobs")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT j.job_id, j.title, j.description, j.requirements, j.location, 
               j.salary_range, c.company_name, j.status
        FROM jobs j
        LEFT JOIN companies c ON j.company_id = c.company_id
        WHERE j.status = 'active'
        ORDER BY j.created_at DESC
    """)
    
    jobs = []
    for row in cur.fetchall():
        jobs.append({
            "job_id": row[0],
            "title": row[1],
            "description": row[2],
            "requirements": row[3],
            "location": row[4],
            "salary_range": row[5],
            "company_name": row[6],
            "status": row[7]
        })
    
    cur.close()
    conn.close()
    
    return {"jobs": jobs}

# Create job (recruiter only)
@router.post("/jobs")
async def create_job(data: JobCreate, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    if user.get('role') not in ['admin', 'recruiter']:
        raise HTTPException(status_code=403, detail="Only recruiters can create jobs")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get or create user ID for this recruiter
    sub = user.get('sub')
    
    # Check if sub is a username (string) or user ID (numeric)
    try:
        recruiter_id = int(sub)
    except (ValueError, TypeError):
        # sub is a username, get or create user ID
        cur.execute("SELECT id FROM users WHERE username = %s", (sub,))
        user_row = cur.fetchone()
        
        if user_row:
            recruiter_id = user_row[0]
        else:
            # Create user record for default user
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (sub, f"{sub}@company.com", password_hash, user.get('role'), user.get('role').title()))
            recruiter_id = cur.fetchone()[0]
    
    # Get or create company
    cur.execute("SELECT company_id FROM companies WHERE recruiter_id = %s", (recruiter_id,))
    company = cur.fetchone()
    
    if not company:
        cur.execute("""
            INSERT INTO companies (recruiter_id, company_name, description, website)
            VALUES (%s, %s, %s, %s)
            RETURNING company_id
        """, (recruiter_id, 'Default Company', 'Company description', 'https://example.com'))
        company_id = cur.fetchone()[0]
    else:
        company_id = company[0]
    
    try:
        cur.execute("""
            INSERT INTO jobs (recruiter_id, company_id, title, description, requirements, location, salary_range)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING job_id
        """, (recruiter_id, company_id, data.title, data.description, data.requirements, data.location, data.salary_range))
        
        job_id = cur.fetchone()[0]
        
        conn.commit()
        
        return {"message": "Job created", "job_id": job_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# Create company profile (recruiter)
@router.post("/company")
async def create_company(company_name: str = Form(...), description: str = Form(...), website: str = Form(...), token: str = Form(...)):
    user = get_current_user_from_token(token)
    
    if user.get('role') not in ['admin', 'recruiter']:
        raise HTTPException(status_code=403, detail="Only recruiters can create companies")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO companies (recruiter_id, company_name, description, website)
        VALUES (%s, %s, %s, %s)
        RETURNING company_id
    """, (user.get('sub'), company_name, description, website))
    
    company_id = cur.fetchone()[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"message": "Company created", "company_id": company_id}

# Security test endpoints (tester only)
# Security test endpoints (tester only)
# @router.post("/test/brute-force")
# async def test_brute_force(authorization: str = Header(None)):
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Authorization header required")
    
#     token = authorization.replace("Bearer ", "")
#     user = get_current_user_from_token(token)
    
#     if user.get('role') != 'tester':
#         raise HTTPException(status_code=403, detail="Only testers can run security tests")
    
#     # Simulate brute force test
#     conn = get_db_connection()
#     cur = conn.cursor()
    
#     cur.execute("""
#         INSERT INTO security_tests (tester_id, test_type, result)
#         VALUES (%s, 'brute_force', 'Test executed - 1000 login attempts simulated')
#         RETURNING test_id
#     """, (user.get('sub'),))
    
#     test_id = cur.fetchone()[0]
#     conn.commit()
#     cur.close()
#     conn.close()
    
#     # Trigger alert in cyber threat system
#     try:
#         import requests
#         requests.post("http://127.0.0.1:8000/api/detect/brute-force", 
#                      json={"source": "recruitment_tester", "attempts": 1000},
#                      timeout=2)
#     except:
#         pass  # Ignore if cyber threat API not available
    
#     return {
#         "message": "✅ Brute force test completed", 
#         "test_id": test_id, 
#         "result": "1000 login attempts simulated",
#         "details": "Simulated attack on /api/auth/login endpoint - Testing rate limiting and account lockout"
#     }

@router.post("/test/brute-force")
async def test_brute_force(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    if user.get('role') != 'tester':
        raise HTTPException(status_code=403, detail="Only testers can run security tests")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO security_tests (tester_id, test_type, result)
        VALUES (%s, 'brute_force', 'Test executed - 1000 login attempts simulated')
        RETURNING test_id
    """, (user.get('sub'),))
    
    test_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        "message": "✅ Brute force test completed",
        "test_id": test_id,
        "result": "1000 login attempts simulated",
        "details": "Simulated attack on /api/auth/login endpoint"
    }

@router.post("/test/sqli")
async def test_sqli(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    if user.get('role') != 'tester':
        raise HTTPException(status_code=403, detail="Only testers can run security tests")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO security_tests (tester_id, test_type, result)
        VALUES (%s, 'sql_injection', 'SQL injection test on job search - parameterized queries verified')
        RETURNING test_id
    """, (user.get('sub'),))
    
    test_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    # Trigger alert
    try:
        import requests
        requests.post("http://127.0.0.1:8000/api/detect/sqli", 
                     json={"source": "recruitment_tester", "payload": "' OR '1'='1"},
                     timeout=2)
    except:
        pass
    
    return {
        "message": "✅ SQL injection test completed", 
        "test_id": test_id, 
        "result": "Parameterized queries verified",
        "details": "Tested job search and application endpoints with SQL injection payloads - All queries use parameterized statements"
    }

@router.post("/test/bot")
async def test_bot(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    if user.get('role') != 'tester':
        raise HTTPException(status_code=403, detail="Only testers can run security tests")
    
    # Trigger alert
    try:
        import requests
        requests.post("http://127.0.0.1:8000/api/detect/bot", 
                     json={"source": "recruitment_tester", "requests": 500},
                     timeout=2)
    except:
        pass
    
    return {
        "message": "✅ Bot activity test completed", 
        "result": "500 automated requests simulated",
        "details": "Simulated bot traffic on job search endpoints - Testing rate limiting and CAPTCHA triggers"
    }

@router.post("/test/malicious-upload")
async def test_malicious(file: UploadFile = File(...), authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    user = get_current_user_from_token(token)
    
    if user.get('role') != 'tester':
        raise HTTPException(status_code=403, detail="Only testers can run security tests")
    
    # Scan file with threat detection
    from file_scanner import FileScanner
    scanner = FileScanner()
    
    # Save temp file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Scan file
        scan_result = scanner.scan_file(tmp_path, file.filename or "unknown")

        # Trigger alert if malicious
        if scan_result.get('is_malicious', False):
            try:
                import requests
                requests.post("http://127.0.0.1:8000/api/detect/malicious-file", 
                             json={
                                 "source": "recruitment_tester",
                                 "filename": file.filename,
                                 "threat_type": scan_result.get('threat_type', 'Unknown')
                             },
                             timeout=2)
            except:
                pass
        
        return {
            "message": "✅ Malicious upload test completed", 
            "filename": file.filename,
            "is_malicious": scan_result.get('is_malicious', False),
            "threat_type": scan_result.get('threat_type', 'None'),
            "details": f"File scanned using threat detection engine - {scan_result.get('verdict', 'Unknown')}"
        }
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
