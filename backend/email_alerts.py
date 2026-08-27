import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class EmailAlertSender:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.alert_email = os.getenv("ALERT_EMAIL", "admin@securehire.com")
    
    def send_alert_email(self, alert_data):
        """Send email alert for critical threats"""
        if not self.sender_email or not self.sender_password:
            print("Email not configured - skipping alert")
            return False
        print(f"Email config: {self.sender_email}, {self.smtp_server}, {self.smtp_port}")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.alert_email
            msg['Subject'] = f"🚨 CRITICAL ALERT: {alert_data['category']}"
            
            # Email body
            body = self._create_email_body(alert_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"Alert email sent to {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"Email send error: {e}")
            return False
    
    def _create_email_body(self, alert_data):
        """Create HTML email body"""
        severity_color = {
            "Critical": "#ff4444",
            "High": "#ff8800",
            "Medium": "#ffcc00",
            "Low": "#44aa44"
        }
        
        color = severity_color.get(alert_data.get("severity", "Medium"), "#ff8800")
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                <h1>🚨 Security Alert</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2>Alert Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Alert ID</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert_data.get('alert_id', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Category</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert_data.get('category', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Severity</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: {color}; font-weight: bold;">{alert_data.get('severity', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Risk Score</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert_data.get('risk_score', 'N/A')}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Reason</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert_data.get('reason', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Recommended Response</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert_data.get('recommended_response', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Timestamp</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert_data.get('timestamp', 'N/A')}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-left: 4px solid {color};">
                    <h3>⚠️ Immediate Action Required</h3>
                    <p>This is an automated alert from SecureHire Security System. Please investigate and take appropriate action.</p>
                </div>
            </div>
            
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #666;">
                <p>SecureHire Security System | Automated Alert</p>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def send_test_email(self):
        """Send test email to verify configuration"""
        test_alert = {
            "alert_id": "TEST001",
            "category": "Test Alert",
            "severity": "High",
            "risk_score": 50,
            "reason": "This is a test alert to verify email configuration",
            "recommended_response": "No action needed - this is a test",
            "timestamp": "2026-08-20 22:45:00"
        }
        
        return self.send_alert_email(test_alert)