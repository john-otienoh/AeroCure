import logging
import sys
from threading import Thread

from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""
    SANDBOX_API_KEY: str
    SANDBOX_USERNAME: str = "sandbox"               
    SMS_SHORTCODE: str = "90875"
    AT_MESSAGING_URL: str = "https://api.sandbox.africastalking.com/version1/messaging"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

load_dotenv() 

try:
    settings = Settings()
except ValidationError as e:
    print("Configuration error:", e, file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("aerocure.sms")

app = Flask(__name__)
def send_sms(phone_number: str, message: str) -> bool:
    """
    Send an SMS via Africa's Talking.
    Returns True on success, False otherwise.
    """
    data = {
        "username": settings.SANDBOX_USERNAME,
        "to": phone_number,
        "message": message,
        "from": settings.SMS_SHORTCODE,
    }
    headers = {
        "apiKey": settings.SANDBOX_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        resp = requests.post(
            settings.AT_MESSAGING_URL,
            headers=headers,
            data=data,
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("SMS sent to %s - status: %s", phone_number, resp.status_code)
        return True
    except requests.RequestException as exc:
        logger.error("Failed to send SMS to %s: %s", phone_number, exc)
        return False
def send_sms_async(phone_number: str, message: str) -> None:
    """Fire-and-forget SMS sending in a background thread."""
    thread = Thread(target=send_sms, args=(phone_number, message))
    thread.start()

@app.route("/sms_callback", methods=["POST"])
def sms_callback():
    """
    Africa's Talking POSTs form data:
      - from   : sender's phone number
      - text   : message body
    We echo the received text back.
    """
    sender = request.form.get("from")
    text = request.form.get("text")

    if not sender or not text:
        logger.warning("Invalid callback - missing 'from' or 'text'")
        return jsonify({"error": "missing fields"}), 400

    if not sender.startswith("+"):
        sender = "+" + sender

    logger.debug("Received SMS from %s: %s", sender, text)

    send_sms_async(sender, text)
    return jsonify({"status": "accepted"}), 200

@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    logger.info("Starting Flask development server (not for production)")
    app.run(host="0.0.0.0", port=5000, debug=False)
