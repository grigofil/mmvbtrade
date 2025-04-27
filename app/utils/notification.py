import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
from app.utils.logger import Logger

logger = Logger(name="notification")

class Notifier:
    """
    Notification manager for MMV Trading Bot
    Handles sending notifications via different channels (email, telegram)
    """
    
    def __init__(self, config):
        """
        Initialize notification manager with config
        
        Args:
            config: Configuration object with notification settings
        """
        self.config = config
        self.email_enabled = config.ENABLE_EMAIL_NOTIFICATIONS
        self.telegram_enabled = config.ENABLE_TELEGRAM_NOTIFICATIONS
        
        # Email settings
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_username = config.SMTP_USERNAME
        self.smtp_password = config.SMTP_PASSWORD
        self.notification_email = config.NOTIFICATION_EMAIL
        
        # Telegram settings
        self.telegram_bot_token = config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID
    
    def send_notification(self, subject, message, level="info", include_trace=False):
        """
        Send notification through all enabled channels
        
        Args:
            subject (str): Notification subject
            message (str): Notification message
            level (str): Message importance level (info, warning, error, critical)
            include_trace (bool): Whether to include stack trace (for errors)
        
        Returns:
            dict: Results of notification attempts
        """
        results = {
            "email": False,
            "telegram": False
        }
        
        # Add stack trace for error notifications if requested
        if include_trace:
            message += "\n\nStack Trace:\n" + traceback.format_exc()
        
        # Log notification
        log_method = getattr(logger, level, logger.info)
        log_method(f"Notification - {subject}: {message}")
        
        # Send via email
        if self.email_enabled:
            try:
                results["email"] = self._send_email(subject, message, level)
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
        
        # Send via Telegram
        if self.telegram_enabled:
            try:
                results["telegram"] = self._send_telegram(subject, message, level)
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {str(e)}")
        
        return results
    
    def _send_email(self, subject, message, level="info"):
        """
        Send notification via email
        
        Args:
            subject (str): Email subject
            message (str): Email body
            level (str): Message importance level
        
        Returns:
            bool: Success status
        """
        if not self.email_enabled:
            return False
        
        # Create multipart message
        msg = MIMEMultipart()
        msg['From'] = self.smtp_username
        msg['To'] = self.notification_email
        
        # Add level prefix to subject
        level_prefix = level.upper() if level != "info" else ""
        if level_prefix:
            msg['Subject'] = f"[{level_prefix}] {subject}"
        else:
            msg['Subject'] = subject
        
        # Add HTML body
        body = self._format_email_body(message, level)
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server and send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email notification sent: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _send_telegram(self, subject, message, level="info"):
        """
        Send notification via Telegram
        
        Args:
            subject (str): Message subject
            message (str): Message content
            level (str): Message importance level
        
        Returns:
            bool: Success status
        """
        if not self.telegram_enabled:
            return False
        
        # Format message for Telegram
        level_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = level_emoji.get(level, "ℹ️")
        telegram_message = f"{emoji} *{subject}*\n\n{message}"
        
        # Send Telegram message
        api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": telegram_message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(api_url, data=payload)
            if response.status_code == 200:
                logger.info(f"Telegram notification sent: {subject}")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    def _format_email_body(self, message, level="info"):
        """
        Format email body with HTML styling based on level
        
        Args:
            message (str): Message content
            level (str): Message importance level
        
        Returns:
            str: Formatted HTML body
        """
        # Define colors for different levels
        level_colors = {
            "info": "#007bff",
            "warning": "#ffc107",
            "error": "#dc3545",
            "critical": "#7d0000"
        }
        
        color = level_colors.get(level, level_colors["info"])
        
        # Format message as HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ padding: 20px; }}
                .header {{ color: white; background-color: {color}; padding: 10px; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 15px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{level.upper() if level != "info" else "NOTIFICATION"}</h2>
                </div>
                <div class="content">
                    {message.replace('\n', '<br>')}
                </div>
                <div class="footer">
                    <p>This is an automated message from MMV Trading Bot. Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    # Convenience methods for different notification levels
    def info(self, subject, message):
        """Send info notification"""
        return self.send_notification(subject, message, "info")
    
    def warning(self, subject, message):
        """Send warning notification"""
        return self.send_notification(subject, message, "warning")
    
    def error(self, subject, message, include_trace=True):
        """Send error notification"""
        return self.send_notification(subject, message, "error", include_trace)
    
    def critical(self, subject, message, include_trace=True):
        """Send critical notification"""
        return self.send_notification(subject, message, "critical", include_trace)
    
    def trade_executed(self, trade_data):
        """
        Send notification about executed trade
        
        Args:
            trade_data (dict): Trade details including symbol, side, price, quantity
        """
        symbol = trade_data.get('symbol', 'Unknown')
        side = trade_data.get('side', 'Unknown').upper()
        price = trade_data.get('price', 0)
        quantity = trade_data.get('quantity', 0)
        total = float(price) * float(quantity)
        
        subject = f"Trade Executed: {side} {symbol}"
        message = f"""
Trade details:
- Symbol: {symbol}
- Side: {side}
- Price: ${price}
- Quantity: {quantity}
- Total: ${total:.2f}
        """
        
        return self.info(subject, message)
    
    def strategy_signal(self, strategy_name, symbol, signal_type, details=None):
        """
        Send notification about strategy signal
        
        Args:
            strategy_name (str): Strategy that generated the signal
            symbol (str): Trading pair symbol
            signal_type (str): Signal type (buy, sell, etc.)
            details (dict): Additional signal details
        """
        subject = f"Signal: {signal_type.upper()} on {symbol}"
        
        details_text = ""
        if details:
            details_text = "\nSignal details:\n"
            for key, value in details.items():
                details_text += f"- {key}: {value}\n"
        
        message = f"""
Strategy {strategy_name} generated a {signal_type.upper()} signal for {symbol}.
{details_text}
        """
        
        return self.info(subject, message) 