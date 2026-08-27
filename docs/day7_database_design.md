\# Day 7 Database Design



\## Database Name

cyber\_recruitment\_db



\## Tables



\### activity\_logs

Stores user activity such as login and resume upload.



Columns:

\- id (SERIAL PRIMARY KEY)

\- timestamp (TIMESTAMP)

\- event\_type (TEXT)

\- email (TEXT)

\- ip\_address (TEXT)

\- status (TEXT)

\- details (TEXT)



\### alerts

Stores generated security alerts.



Columns:

\- id (SERIAL PRIMARY KEY)

\- alert\_id (TEXT)

\- timestamp (TIMESTAMP)

\- category (TEXT)

\- severity (TEXT)

\- risk\_score (INTEGER)

\- confidence (NUMERIC)

\- reason (TEXT)

\- recommended\_response (TEXT)

\- log\_entry (TEXT)



\## Notes

\- All timestamps use the server time.

\- The current version does not store real passwords.

\- The system uses parameterized queries to avoid SQL injection.

