import os
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)


def send_sms_otp(phone_number, otp_code, message=None):
    try:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")

        if not account_sid or not auth_token or not twilio_phone_number:
            logger.warning(
                "Twilio credentials not fully configured. Assuming development mode and skipping SMS."
            )
            print(f"[DEBUG] OTP for {phone_number}: {otp_code}")
            return True

        client = Client(account_sid, auth_token)

        body_text = (
            message if message else f"Your Tybee verification code is: {otp_code}"
        )

        msg = client.messages.create(
            body=body_text, from_=twilio_phone_number, to=phone_number
        )
        logger.info(f"OTP sent to {phone_number}, SID: {msg.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP to {phone_number} via Twilio: {str(e)}")
        # We might want to handle this gracefully, for now we log it and print to console as fallback
        print(f"[DEBUG FALLBACK] OTP for {phone_number}: {otp_code}")
        return False
