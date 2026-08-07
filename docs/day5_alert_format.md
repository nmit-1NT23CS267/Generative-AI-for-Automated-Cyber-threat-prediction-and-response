# Alert Format

Each alert contains the following information:

- alert_id: Unique identifier for the alert.
- timestamp: Time when the alert was generated.
- category: Type of suspected threat.
- severity: Risk level of the threat.
- risk_score: Numeric score from 0 to 100.
- confidence: Confidence of the detection rule.
- reason: Explanation of why the event was detected.
- recommended_response: Suggested action for the administrator.
- log: Original event that caused the alert.

## Severity Meaning

### Low
A suspicious event that requires observation.

### Medium
An event that may require investigation.

### High
A strong indication of malicious or unauthorized activity.

### Critical
A potentially dangerous attack that requires immediate attention.

## Example

A SQL Injection alert should explain that a suspicious SQL pattern was found and recommend rejecting the input and using parameterized database queries.
