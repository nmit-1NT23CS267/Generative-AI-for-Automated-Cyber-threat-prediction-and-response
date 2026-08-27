from database import get_db_connection


def create_tables():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                event_type TEXT,
                email TEXT,
                ip_address TEXT,
                status TEXT,
                details TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                alert_id TEXT,
                timestamp TIMESTAMP,
                category TEXT,
                severity TEXT,
                risk_score INTEGER,
                confidence NUMERIC,
                reason TEXT,
                recommended_response TEXT,
                log_entry TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_accounts (
                id SERIAL PRIMARY KEY,
                role TEXT,
                name TEXT,
                email TEXT,
                password TEXT,
                company TEXT,
                role_title TEXT,
                experience TEXT,
                skills TEXT,
                team TEXT,
                created_at TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidate_applications (
                id SERIAL PRIMARY KEY,
                candidate_name TEXT,
                candidate_email TEXT,
                job_title TEXT,
                company TEXT,
                resume_file_name TEXT,
                resume_data TEXT,
                applied_at TIMESTAMP,
                malicious_flag BOOLEAN DEFAULT FALSE,
                status TEXT
            )
        """)
        conn.execute("""
                CREATE TABLE IF NOT EXISTS security_tests (
                test_id SERIAL PRIMARY KEY,
                tester_id TEXT,
                test_type TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    print("Tables created successfully.")


if __name__ == "__main__":
    create_tables()