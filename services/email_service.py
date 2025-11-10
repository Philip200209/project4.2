import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template
import logging

class EmailService:
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
    def init_app(self, app):
        """Initialize with Flask app configuration"""
        self.config = app.config
        self.logger.info("📧 EmailService initialized with config")
        
    def send_email(self, to_email, subject, template, **template_data):
        """Send email using template"""
        try:
            self.logger.info(f"📧 Attempting to send email to: {to_email}")
            self.logger.info(f"📧 Template: {template}, Subject: {subject}")
            
            # Render the email template
            self.logger.info("📧 Rendering template...")
            html_content = render_template(f'email/{template}', **template_data)
            self.logger.info("✅ Template rendered successfully")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.get('MAIL_DEFAULT_SENDER')
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            self.logger.info("📧 Connecting to SMTP server...")
            with smtplib.SMTP(self.config.get('MAIL_SERVER'), self.config.get('MAIL_PORT')) as server:
                server.starttls()
                self.logger.info("📧 Logging in...")
                server.login(
                    self.config.get('MAIL_USERNAME'),
                    self.config.get('MAIL_PASSWORD')
                )
                self.logger.info("📧 Sending message...")
                server.send_message(msg)
                
            self.logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            import traceback
            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return False
    
    def send_payment_reminder(self, to_email, client_name, loan_details, days_until_due):
        """Send payment reminder email"""
        return self.send_email(
            to_email=to_email,
            subject=f"Payment Reminder - {days_until_due} days until due",
            template='payment_reminder.html',
            client_name=client_name,
            loan_details=loan_details,
            days_until_due=days_until_due
        )
    
    def send_risk_alert(self, to_email, client_name, risk_score, loan_amount):
        """Send risk alert email"""
        return self.send_email(
            to_email=to_email,
            subject=f"Risk Alert - High Risk Loan Detected",
            template='risk_alert.html',
            client_name=client_name,
            risk_score=risk_score,
            loan_amount=loan_amount
        )
    
    def send_restructuring_offer(self, to_email, client_name, current_terms, new_terms):
        """Send loan restructuring offer"""
        return self.send_email(
            to_email=to_email,
            subject="Loan Restructuring Offer",
            template='restructuring_offer.html',
            client_name=client_name,
            current_terms=current_terms,
            new_terms=new_terms
        )