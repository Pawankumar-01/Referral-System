import requests
import os
from dotenv import load_dotenv

# This looks for a .env file and loads the variables
load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")



META_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"


def send_whatsapp_message(phone: str, message: str):

    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        print("WhatsApp ENV variables missing")
        return False

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message},
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            META_URL,
            json=payload,
            headers=headers,
            timeout=10
        )

        print("WhatsApp Response Status:", response.status_code)
        print("WhatsApp Response Body:", response.text)

        return response.status_code == 200

    except Exception as e:
        print("WhatsApp Exception:", str(e))
        return False