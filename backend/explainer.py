from datetime import datetime


def explain_threat(alert):
    """
    Generates a human-readable explanation for a security alert.
    """
    category = alert.get("category", "Unknown Threat")
    severity = alert.get("severity", "Unknown")
    risk_score = alert.get("risk_score", 0)
    reason = alert.get("reason", "")
    log_entry = alert.get("log", "")

    explanation = {
        "threat_summary": generate_summary(category, severity, risk_score),
        "why_suspicious": generate_why_suspicious(category, reason, log_entry),
        "immediate_actions": generate_immediate_actions(category),
        "long_term_mitigation": generate_long_term_mitigation(category)
    }

    return explanation


def generate_summary(category, severity, risk_score):
    summaries = {
        "SQL Injection": f"A {severity.lower()} severity SQL injection attempt was detected with risk score {risk_score}.",
        "Cross-Site Scripting": f"A {severity.lower()} severity Cross-Site Scripting (XSS) attempt was detected with risk score {risk_score}.",
        "Brute Force": f"A {severity.lower()} severity brute force attack was detected with risk score {risk_score}.",
        "Bot Activity": f"A {severity.lower()} severity automated bot activity was detected with risk score {risk_score}.",
        "Unauthorized Access": f"A {severity.lower()} severity unauthorized access attempt was detected with risk score {risk_score}."
    }

    return summaries.get(category, f"A {severity.lower()} severity threat was detected with risk score {risk_score}.")


def generate_why_suspicious(category, reason, log_entry):
    explanations = {
        "SQL Injection": f"The input contains SQL injection patterns such as ' OR 1=1 --, UNION SELECT, or DROP TABLE. These patterns are commonly used to bypass authentication or extract database contents. Detected: {reason}",
        "Cross-Site Scripting": f"The input contains HTML or JavaScript patterns such as <script> tags or event handlers. These can execute malicious scripts in users' browsers. Detected: {reason}",
        "Brute Force": f"Multiple failed login attempts were detected from the same user or IP address. This indicates an automated password guessing attack. Detected: {reason}",
        "Bot Activity": f"An unusually high number of requests or downloads were detected from a single source. This behavior is consistent with automated scraping or data exfiltration. Detected: {reason}",
        "Unauthorized Access": f"An unknown or unauthorized user attempted to access a restricted endpoint. This could indicate privilege escalation or reconnaissance. Detected: {reason}"
    }

    return explanations.get(category, f"Suspicious pattern detected: {reason}")


def generate_immediate_actions(category):
    actions = {
        "SQL Injection": [
            "Block the source IP address temporarily.",
            "Review all recent database queries from this session.",
            "Check for any unauthorized data access or modification.",
            "Enable database query logging if not already enabled."
        ],
        "Cross-Site Scripting": [
            "Block the source IP address temporarily.",
            "Review all recent user input submissions.",
            "Check for any stored malicious scripts in the database.",
            "Clear browser cache for affected users if necessary."
        ],
        "Brute Force": [
            "Temporarily lock the targeted user account.",
            "Block the source IP address.",
            "Enable CAPTCHA for login attempts.",
            "Notify the affected user about the attack."
        ],
        "Bot Activity": [
            "Apply rate limiting to the source IP.",
            "Temporarily restrict access to resume download endpoints.",
            "Review access logs for data exfiltration patterns.",
            "Consider implementing CAPTCHA for high-frequency requests."
        ],
        "Unauthorized Access": [
            "Block the source IP address immediately.",
            "Review all actions performed by the unauthorized session.",
            "Audit access control configurations.",
            "Enable additional authentication for restricted endpoints."
        ]
    }

    return actions.get(category, [
        "Review the alert details carefully.",
        "Monitor the source for further suspicious activity.",
        "Document the incident for future analysis."
    ])


def generate_long_term_mitigation(category):
    mitigations = {
        "SQL Injection": [
            "Use parameterized database queries or prepared statements.",
            "Implement input validation on all user inputs.",
            "Deploy a Web Application Firewall (WAF).",
            "Conduct regular security code reviews."
        ],
        "Cross-Site Scripting": [
            "Implement output encoding for all user-generated content.",
            "Use Content Security Policy (CSP) headers.",
            "Sanitize all user inputs before storing or displaying.",
            "Train developers on secure coding practices."
        ],
        "Brute Force": [
            "Implement account lockout after multiple failed attempts.",
            "Use multi-factor authentication (MFA).",
            "Deploy CAPTCHA for login forms.",
            "Monitor and alert on unusual login patterns."
        ],
        "Bot Activity": [
            "Implement rate limiting and request throttling.",
            "Use CAPTCHA for high-frequency actions.",
            "Deploy bot detection and mitigation solutions.",
            "Monitor API usage patterns continuously."
        ],
        "Unauthorized Access": [
            "Implement role-based access control (RBAC).",
            "Use multi-factor authentication for admin endpoints.",
            "Conduct regular access control audits.",
            "Implement principle of least privilege."
        ]
    }

    return mitigations.get(category, [
        "Review and improve security configurations.",
        "Conduct security awareness training.",
        "Implement continuous monitoring."
    ])


def explain_all_alerts(alerts):
    """
    Generates explanations for multiple alerts.
    """
    explanations = []

    for alert in alerts:
        explanation = explain_threat(alert)
        explanation["original_alert"] = alert
        explanations.append(explanation)

    return explanations