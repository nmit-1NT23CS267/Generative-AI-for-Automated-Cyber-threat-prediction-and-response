import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
import json

class ThreatMLDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.user_history = {}
    
    def extract_features(self, user_id, timestamp, ip, user_agent):
        """Extract numerical features from login attempt"""
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        # Check if unusual hour (night time)
        unusual_hour = 1 if hour < 6 or hour > 22 else 0
        
        # Check if weekend
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # IP reputation (simplified)
        ip_score = self._ip_reputation_score(ip)
        
        # User agent complexity
        ua_complexity = len(user_agent) if user_agent else 0
        
        # Login frequency (simplified)
        login_count = self._get_user_login_count(user_id)
        
        return [
            hour,
            unusual_hour,
            day_of_week,
            is_weekend,
            ip_score,
            ua_complexity,
            login_count
        ]
    
    def _ip_reputation_score(self, ip):
        """Simple IP reputation scoring"""
        if ip.startswith("192.168.") or ip.startswith("10."):
            return 1  # Internal IP
        elif ip.startswith("172."):
            return 2  # Private range
        else:
            return 3  # External IP
    
    def _get_user_login_count(self, user_id):
        """Get login count for user (simplified)"""
        return self.user_history.get(user_id, 0)
    
    def train(self, historical_data):
        """Train model on historical data"""
        if len(historical_data) < 10:
            return False
        
        features = []
        for record in historical_data:
            feat = self.extract_features(
                record["user_id"],
                record["timestamp"],
                record["ip_address"],
                record["user_agent"]
            )
            features.append(feat)
        
        X = np.array(features)
        self.model.fit(X)
        return True
    
    def predict(self, user_id, timestamp, ip, user_agent):
        """Predict if login attempt is anomalous"""
        features = self.extract_features(user_id, timestamp, ip, user_agent)
        X = np.array([features])
        
        # -1 = anomaly, 1 = normal
        prediction = self.model.predict(X)[0]
        score = self.model.score_samples(X)[0][0]
        
        is_anomaly = prediction == -1
        confidence = abs(score)
        
        return is_anomaly, confidence, score
    
    def update_history(self, user_id):
        """Update user login history"""
        self.user_history[user_id] = self.user_history.get(user_id, 0) + 1