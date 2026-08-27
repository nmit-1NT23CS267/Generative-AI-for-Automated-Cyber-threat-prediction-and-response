from psycopg import connect
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cyber_user:cyber_password@localhost:5432/cyber_recruitment_db"
)


def get_db_connection():
    """
    Returns a new database connection.
    """
    return connect(DATABASE_URL)