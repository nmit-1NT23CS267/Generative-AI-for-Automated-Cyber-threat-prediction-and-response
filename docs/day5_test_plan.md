# Day 5 Test Plan

## Test Environment
The tests will use synthetic activity logs generated locally. No real external website or system will be attacked.

## Test Scenarios

| Test ID | Scenario | Expected Category | Expected Severity |
|---|---|---|---|
| D5-01 | Normal successful login | No alert | None |
| D5-02 | One failed login | No high-severity alert | Low |
| D5-03 | Three failed logins by one user | Brute Force | High |
| D5-04 | SQL injection-like input | SQL Injection | Critical |
| D5-05 | XSS-like input | Cross-Site Scripting | High |
| D5-06 | Three resume downloads by one source | Bot Activity | High |
| D5-07 | Unknown user accessing admin endpoint | Unauthorized Access | High |
| D5-08 | Repeated identical suspicious event | One deduplicated alert | Same as original |

## Pass Condition
A test passes when the detected category matches the expected category and the severity is equal to or higher than the expected severity.

## Evidence
For every test, save:
- input log or test name,
- detected category,
- severity,
- confidence,
- response recommendation.
