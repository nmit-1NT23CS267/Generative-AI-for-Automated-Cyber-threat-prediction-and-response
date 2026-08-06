# Day 4 Test Cases

| Test ID | Input or Action | Expected Result |
|---|---|---|
| TC01 | One successful login | No threat alert |
| TC02 | One failed login | No high-severity alert |
| TC03 | Three failed logins for one user | Brute-force alert |
| TC04 | Input containing ' OR 1=1 -- | SQL Injection alert |
| TC05 | Input containing <script>alert(1)</script> | XSS alert |
| TC06 | Repeated resume downloads from one IP | Bot activity alert |
| TC07 | Unknown user accesses /admin | Unauthorized access alert |
