import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import app
from threading import Thread
import os
from datetime import datetime

class EmailService:
    @staticmethod
    def send_email(to_email, subject, html_content, text_content=None):
        """
        Send an email using SMTP (stub implementation for demo)
        
        In a real application, this would connect to an SMTP server
        or email service like SendGrid, Mailgun, etc.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
        
        Returns:
            bool: True if email was sent successfully
        """
        # This is a stub implementation for demo purposes
        # In production, you would implement actual email sending
        
        try:
            # Simulate email sending (replace with actual SMTP code)
            print(f"\n=== EMAIL NOTIFICATION ===")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: {text_content or html_content[:100]}...")
            print("=== EMAIL WOULD BE SENT HERE ===\n")
            
            # Log the email attempt
            EmailService.log_email_attempt(to_email, subject, True)
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            EmailService.log_email_attempt(to_email, subject, False, str(e))
            return False

    @staticmethod
    def send_alert_notification(user_email, alert_type, message, account_info=None):
        """
        Send an alert notification email
        
        Args:
            user_email: User's email address
            alert_type: Type of alert (low_balance, large_tx, etc.)
            message: Alert message
            account_info: Account information (optional)
        
        Returns:
            bool: True if email was sent successfully
        """
        subject = f"EverTrust Bank Alert: {alert_type.replace('_', ' ').title()}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>EverTrust Bank Alert</h1>
                </div>
                <div class="content">
                    <h2>{subject}</h2>
                    <p>{message}</p>
                    {f'<p><strong>Account:</strong> {account_info}</p>' if account_info else ''}
                    <p>If you did not initiate this action or have any concerns, 
                    please contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>© {datetime.now().year} EverTrust Bank. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        EverTrust Bank Alert: {subject}
        
        {message}
        
        {f'Account: {account_info}' if account_info else ''}
        
        If you did not initiate this action or have any concerns, 
        please contact our support team immediately.
        
        This is an automated message. Please do not reply to this email.
        © {datetime.now().year} EverTrust Bank. All rights reserved.
        """
        
        return EmailService.send_email(user_email, subject, html_content, text_content)

    @staticmethod
    def send_welcome_email(user_email, user_name):
        """
        Send a welcome email to new users
        
        Args:
            user_email: User's email address
            user_name: User's name
        
        Returns:
            bool: True if email was sent successfully
        """
        subject = "Welcome to EverTrust Bank!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to EverTrust Bank!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Thank you for choosing EverTrust Bank for your financial needs.</p>
                    <p>Your account has been successfully created and is ready to use.</p>
                    <p>With EverTrust Bank, you can:</p>
                    <ul>
                        <li>View account balances and transactions</li>
                        <li>Transfer money between accounts</li>
                        <li>Pay bills online</li>
                        <li>Set up alerts and notifications</li>
                        <li>And much more!</li>
                    </ul>
                    <p>If you have any questions, please don't hesitate to contact our support team.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>© {datetime.now().year} EverTrust Bank. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(user_email, subject, html_content)

    @staticmethod
    def send_transaction_receipt(user_email, transaction_data):
        """
        Send a transaction receipt email
        
        Args:
            user_email: User's email address
            transaction_data: Dictionary containing transaction details
        
        Returns:
            bool: True if email was sent successfully
        """
        subject = f"Transaction Receipt: {transaction_data.get('type', 'Transaction')}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .transaction-details {{ background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #e5e7eb; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Transaction Receipt</h1>
                </div>
                <div class="content">
                    <h2>Your transaction is complete</h2>
                    <div class="transaction-details">
                        <p><strong>Type:</strong> {transaction_data.get('type', 'N/A')}</p>
                        <p><strong>Amount:</strong> ${transaction_data.get('amount', '0.00')}</p>
                        <p><strong>Description:</strong> {transaction_data.get('description', 'N/A')}</p>
                        <p><strong>Date:</strong> {transaction_data.get('date', 'N/A')}</p>
                        <p><strong>Status:</strong> {transaction_data.get('status', 'Completed')}</p>
                        {f'<p><strong>Account:</strong> {transaction_data.get("account", "N/A")}</p>' if transaction_data.get('account') else ''}
                    </div>
                    <p>Thank you for banking with EverTrust.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>© {datetime.now().year} EverTrust Bank. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(user_email, subject, html_content)

    @staticmethod
    def log_email_attempt(to_email, subject, success, error_message=None):
        """
        Log email sending attempts (for audit purposes)
        
        Args:
            to_email: Recipient email
            subject: Email subject
            success: Whether email was sent successfully
            error_message: Error message if failed
        """
        # In a real application, this would log to a database
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'to': to_email,
            'subject': subject,
            'success': success,
            'error': error_message
        }
        
        print(f"Email attempt logged: {log_entry}")

    @staticmethod
    def send_async_email(to_email, subject, html_content, text_content=None):
        """
        Send email asynchronously using a thread
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
        """
        thread = Thread(
            target=EmailService.send_email,
            args=(to_email, subject, html_content, text_content)
        )
        thread.start()