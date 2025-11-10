import africastalking
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("AT_USERNAME", "sandbox")
api_key = os.getenv("AT_API_KEY")

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def send_sms(phone_number, message):
    try:
        response = sms.send(message, [phone_number])
        print("SMS sent:", response)
        return response
    except Exception as e:
        print("SMS error:", e)
        return None
