from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import hashlib
from database import get_db_connection

router = APIRouter()
security = HTTPBearer()

# Default users (admin, recruiter, tester)
DEFAULT_USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "Admin User"
    },
    "recruiter": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "recruiter",
        "name": "HR Recruiter"
    },
    "tester": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "tester",
        "name": "Security Tester"
    }
}

SECRET_KEY = "cyber-threat-secret-key-2026"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    from datetime import datetime
    from database import get_db_connection
    
    password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()

    # Check database first
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role, full_name FROM users WHERE username = %s AND password_hash = %s",
                (login_data.username, password_hash))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        # Database user found
        token = create_token({
            "sub": str(user[0]),  # user_id
            "role": user[1]
        })

        # Log activity
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO activity_logs (timestamp, event_type, email, ip_address, status, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (datetime.now(), 'login', login_data.username, '127.0.0.1', 'success', f'User {login_data.username} logged in as {user[1]}'))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Log error: {e}")

        return Token(
            access_token=token,
            token_type="bearer",
            role=user[1],
            username=login_data.username
        )

    # Check default users (admin, recruiter, tester)
    if login_data.username in DEFAULT_USERS:
        default_user = DEFAULT_USERS[login_data.username]

        if default_user["password"] != password_hash:
            # Log failed login
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO activity_logs (timestamp, event_type, email, ip_address, status, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (datetime.now(), 'login', login_data.username, '127.0.0.1', 'failed', 'Invalid password'))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Log error: {e}")
            
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_token({
            "sub": login_data.username,
            "role": default_user["role"]
        })

        # Log successful login
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO activity_logs (timestamp, event_type, email, ip_address, status, details)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (datetime.now(), 'login', login_data.username, '127.0.0.1', 'success', f'Default user {login_data.username} logged in'))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Log error: {e}")

        return Token(
            access_token=token,
            token_type="bearer",
            role=default_user["role"],
            username=login_data.username
        )

    # Log invalid user
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO activity_logs (timestamp, event_type, email, ip_address, status, details)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (datetime.now(), 'login', login_data.username, '127.0.0.1', 'failed', 'User not found'))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Log error: {e}")

    raise HTTPException(status_code=401, detail="Invalid credentials")

def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")