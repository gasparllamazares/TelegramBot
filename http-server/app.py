from bottle import Bottle, request, response
from database import get_user_id
from bot_instance import bot  # Import the bot instance

# Initialize Bottle app
app = Bottle()

@app.route('/send_sms', method='GET')
def send_sms():
    # Retrieve parameters from the URL query string
    username = request.query.username
    message = request.query.message

    # Validate that both parameters are provided
    if not username or not message:
        response.status = 400  # Bad request
        return {"error": "Both 'username' and 'message' query parameters are required"}

    # Lookup the user's Telegram ID in the database
    user_id = get_user_id(username)
    if not user_id:
        response.status = 404  # Not found
        return {"error": "User not found. Make sure the username is registered."}

    # Send the message using telebot
    try:
        bot.send_message(chat_id=user_id, text=message)
        return {"status": "Message sent"}
    except Exception as e:
        response.status = 500  # Internal server error
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)
