-- Test 1: View recent activity logs
SELECT id, timestamp, event_type, email, status
FROM activity_logs
ORDER BY timestamp DESC
LIMIT 10;

-- Test 2: Count alerts by category
SELECT category, COUNT(*) AS alert_count
FROM alerts
GROUP BY category;

-- Test 3: View high-severity alerts
SELECT alert_id, category, severity, risk_score, reason
FROM alerts
WHERE severity IN ('High', 'Critical')
ORDER BY risk_score DESC;