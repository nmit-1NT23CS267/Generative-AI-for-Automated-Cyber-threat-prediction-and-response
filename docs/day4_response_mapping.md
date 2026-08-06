# Threat Response Mapping

| Threat | Suggested Response |
|---|---|
| Brute Force | Temporarily restrict login and alert admin |
| SQL Injection | Reject input and use parameterized database queries |
| XSS | Reject or sanitize input and alert admin |
| Bot Activity | Apply rate limiting or temporary IP restriction |
| Unauthorized Access | Deny access and alert admin |

The Day 4 version only generates response suggestions. Actual permanent IP blocking will be implemented later after the detection system is tested.
