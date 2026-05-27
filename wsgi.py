from flask import Flask, request
import requests
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Africa's Talking Sandbox Credentials
API_KEY = os.getenv("SANDBOX_API_KEY")
USERNAME = os.getenv("SANDBOX_USERNAME")
SHORT_CODE = os.getenv('SMS_SHORTCODE')
URL = "https://api.sandbox.africastalking.com/version1/messaging"

HEADERS = {
    'apiKey': API_KEY, #
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded' #
}

@app.route('/')
def hello():
    return 'Hello AeroCure'


@app.route("/sms_callback", methods = ['POST'])
def sms_callback():
    """
    Africa's Talking sends data as form-encoded data
    'from' is the phone number of the person who sent the text
    'text' is the message body they sent"""
    print(request.form)
    sender_phone = request.form.get('from')
    received_text = request.form.get('text')

    data = {
        'username': USERNAME,
        'to': sender_phone,
        'message': received_text, 
        'from': SHORT_CODE
    }
    requests.post(URL, headers=HEADERS, data=data)
    return "Success", 201


if __name__ == '__main__':
    app.run(debug=True)
