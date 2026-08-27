\# Day 6 Frontend Flow



\## Login Flow

1\. User enters email and password.

2\. Frontend sends data to POST /login.

3\. Backend checks the password.

4\. Backend writes a login event to activity.log.

5\. Frontend displays the login status.



\## Resume Upload Flow

1\. User enters email.

2\. User selects a PDF, DOC, or DOCX file.

3\. Frontend creates a FormData object.

4\. Frontend sends the file to POST /upload-resume.

5\. Backend validates and stores the file.

6\. Frontend displays the upload result.



\## Alert Flow

1\. User clicks Analyze Logs.

2\. Frontend sends a request to POST /analyze.

3\. Backend checks activity.log.

4\. Backend creates alerts and saves alerts.json.

5\. Frontend displays the alert count and results.



\## Activity Log Flow

1\. User clicks View Logs.

2\. Frontend requests GET /logs.

3\. Backend returns stored activity logs.

4\. Frontend displays the logs.



\## Available Endpoints

\- POST /login

\- POST /upload-resume

\- GET /logs

\- POST /analyze

\- GET /alerts

