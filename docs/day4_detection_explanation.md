# Detection and Response Explanation

The system receives activity logs from the job portal. Each log contains information such as timestamp, user, IP address, action, status, and details.

The detection module checks these logs for suspicious patterns. It uses simple rules in the first version because rules are easy to understand, test, and explain.

When a suspicious event is found, the system creates an alert. The alert contains the threat category, severity, confidence score, affected user or IP address, reason, and recommended response.

## Example

If a user fails to log in three times from the same IP address, the system classifies the behavior as a possible brute-force attack.

If a request contains a script tag, the system classifies it as a possible XSS attack.

If an IP address downloads many resumes repeatedly, the system classifies it as possible bot activity or resume scraping.
