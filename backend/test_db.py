from database import get_db_connection

# Test connection
try:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = cur.fetchall()
            print("✅ Database connected!")
            print("Tables:", [t[0] for t in tables])
except Exception as e:
    print(f"❌ Database error: {e}")