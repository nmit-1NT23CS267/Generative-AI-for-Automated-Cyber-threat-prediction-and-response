# Day 5 Testing Report

The system was tested using synthetic activity logs representing normal and suspicious behavior. The tests included brute-force login attempts, SQL injection-like input, XSS-like input, bot-based resume downloads, and unauthorized admin access.

The purpose of the tests was to verify that the system:
- detects the correct threat category,
- assigns an appropriate severity,
- provides a confidence value,
- recommends a response,
- and avoids generating repeated duplicate alerts.

The tests were performed locally against the project application. No external systems were targeted.
