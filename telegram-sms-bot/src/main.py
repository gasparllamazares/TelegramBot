from bottle import Bottle, request, response
import requests
from database import get_user_id  # Import the helper function
import os, dotenv

# Initialize the Bottle application
app = Bottle()
# Load environment variables
dotenv.load_dotenv()
# Set your Telegram bot token as an environment variable
TELEGRAM_SMS_BOT_TOKEN = os.getenv("TELEGRAM_SMS_BOT_TOKEN")

# Define the base URL of the Telegram API
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_SMS_BOT_TOKEN}"

# Route to send a message to a Telegram user using GET method
@app.route('/send_message', method='GET')
def send_message():
    try:
        # Get username and message from query parameters
        username = request.args.get('username')
        message_text = request.args.get('message_text')

        if not username or not message_text:
            response.status = 400
            return {"error": "username and message query parameters are required"}

        # Lookup the user_id from the database using the username
        user_id = get_user_id(username)
        if not user_id:
            response.status = 404
            return {"error": "User not found. Make sure the username is registered."}

        # Build the URL to send the message
        url = f"{TELEGRAM_API_URL}/sendMessage"

        # Data for the GET request to the Telegram API
        params = {
            "chat_id": user_id,
            "text": message_text
        }
        print(params)

        # Send the request to the Telegram API
        res = requests.get(url, params=params)

        # Check Telegram's response
        if res.status_code == 200:
            return {"status": "Message sent successfully"}
        else:
            response.status = res.status_code
            return res.json()

    except Exception as e:
        response.status = 500
        return {"error": str(e)}

# Run the Bottle application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)
