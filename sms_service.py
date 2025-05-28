import os
import africastalking
from fastapi import HTTPException
from typing import List

# Initialize SDK (you might want to move these to config)
username = "masterclass"  # Your Africa's Talking username
AFRICASTALKING_APIKEY = os.getenv("AFRICASTALKING_APIKEY") # Your API key from the dashboard 

class SMSService:
    def __init__(self):
        africastalking.initialize(username, AFRICASTALKING_APIKEY)
        self.sms = africastalking.SMS

    def send_sms(self, message: str, recipients: List[str], sender_id: str = "Masterclass"):
        try:
            response = self.sms.send(message, recipients, sender_id=sender_id)
            return {
                "status": "success",
                "data": response,
                "message": "SMS sent successfully"
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"SMS sending failed: {str(e)}"
            )

sms_service = SMSService()
