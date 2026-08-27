\# Day 7 Database Documentation



\## Purpose

The PostgreSQL database stores activity logs and security alerts in a structured format. This allows the system to query historical data, perform analysis, and generate reports.



\## Connection Details

\- Host: localhost

\- Port: 5432

\- Database: cyber\_recruitment\_db

\- User: cyber\_user

\- Password: cyber\_password



\## Tables



\### activity\_logs

The activity\_logs table stores login events, resume uploads, and other user actions.



\### alerts

The alerts table stores detected threats, including category, severity, risk score, and recommended response.



\## Security Note

The current version uses parameterized queries to prevent SQL injection. However, the database credentials are stored locally for academic demonstration only.

