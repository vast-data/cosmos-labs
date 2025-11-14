import logging
import requests
from typing import Optional


class TwilioClient:
    """Twilio SMS client for sending safety alerts"""

    def __init__(self, settings):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.messaging_service_sid = settings.twilio_messaging_service_sid
        self.to_phone = settings.twilio_to_phone
        
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        
        logging.info(f"[TWILIO] Initialized Twilio client - Messaging Service: {self.messaging_service_sid}")
        logging.info(f"[TWILIO] Alerts will be sent to: {self.to_phone}")

    def send_sms(self, message: str) -> bool:
        """
        Send SMS alert via Twilio
        
        Returns True if SMS was sent successfully, False otherwise
        """
        try:
            logging.info(f"[TWILIO] Sending SMS alert")
            logging.info(f"[TWILIO] Message preview: {message[:50]}...")
            
            payload = {
                "To": self.to_phone,
                "MessagingServiceSid": self.messaging_service_sid,
                "Body": message
            }
            
            response = requests.post(
                self.api_url,
                data=payload,
                auth=(self.account_sid, self.auth_token),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                sms_sid = response_data.get("sid", "unknown")
                logging.info(f"[TWILIO] SMS sent successfully - SID: {sms_sid}")
                return True
            else:
                logging.error(f"[TWILIO] Failed to send SMS - Status: {response.status_code}")
                logging.error(f"[TWILIO] Response: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"[TWILIO] Error sending SMS: {e}", exc_info=True)
            return False

