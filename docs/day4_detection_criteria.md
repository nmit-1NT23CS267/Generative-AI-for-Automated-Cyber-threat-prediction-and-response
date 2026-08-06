# Day 4 Detection Criteria

## 1. Brute-force login
Condition:
The same email or user has three or more failed login attempts.

Threat category:
Brute Force / Unauthorized Access

Severity:
High

Response:
Temporarily restrict login and generate an alert.

## 2. SQL Injection
Condition:
The input contains suspicious patterns such as:
- OR 1=1
- UNION SELECT
- DROP TABLE
- SQL comments

Threat category:
SQL Injection

Severity:
Critical

Response:
Reject the request, record the event, and alert the administrator.

## 3. Cross-Site Scripting
Condition:
The input contains HTML or JavaScript patterns such as:
- <script>
- javascript:
- onerror=
- onload=

Threat category:
Cross-Site Scripting

Severity:
High

Response:
Reject or sanitize the input, record the event, and generate an alert.

## 4. Bot activity
Condition:
The same user or IP performs many repeated actions such as resume downloads or search requests.

Threat category:
Bot Activity / Resume Scraping

Severity:
High

Response:
Apply throttling, restrict access, and alert the administrator.

## 5. Unauthorized access
Condition:
An unknown user accesses a restricted endpoint or receives a 401/403 response.

Threat category:
Unauthorized Access

Severity:
High

Response:
Block or restrict access and generate an alert.
