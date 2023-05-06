from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Read environment variables
CRYPTO_COM_API_KEY = os.getenv("CRYPTO_COM_API_KEY")
CRYPTO_COM_API_SECRET = os.getenv("CRYPTO_COM_API_SECRET")
TRADINGVIEW_WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")


# Helper function to process the received alert
def process_alert(alert_data):
    # Implement your logic to process the alert and perform trading actions
    pass


@app.route("/webhook", methods=["POST"])
def webhook():
    # Validate webhook secret
    webhook_secret = request.headers.get("X-Webhook-Secret")
    if webhook_secret != TRADINGVIEW_WEBHOOK_SECRET:
        return jsonify({"error": "Invalid webhook secret"}), 403

    # Process the alert based on the Content-Type header
    content_type = request.content_type
    if content_type == "application/json":
        alert_data = request.get_json()
    elif content_type == "text/plain":
        alert_data = request.data.decode("utf-8")
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    # Process the alert
    process_alert(alert_data)

    return jsonify({"message": "Webhook received and processed"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
