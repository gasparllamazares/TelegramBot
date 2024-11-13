from telebot.types import ReplyKeyboardMarkup
from database import save_user, get_user_id, delete_user
import bot_instance

# Cargar el bot del bot_instance
bot = bot_instance.bot


@bot.message_handler(commands=["start"])
def start(message):
    welcome_text = (
        "¡Bienvenido al Bot de SMS a Telegram!\n\n"
        "Este bot permite que cualquier persona pueda enviarte un mensaje "
        "a través de un SMS y que llegue directamente a tu Telegram, siempre que "
        "estés registrado.\n\n"
        "**¿Cómo funciona?**\n"
        "1. Cualquiera puede enviar un SMS al número específico del servicio con el "
        "formato:\n\n"
        "   `[nombre_de_usuario] [mensaje]`\n\n"
        "2. El bot buscará el `nombre_de_usuario` en su lista de usuarios registrados.\n"
        "3. Si encuentra una coincidencia, enviará el mensaje a ese usuario en Telegram.\n\n"
        "Este sistema te permite recibir mensajes SMS de una manera más cómoda en Telegram.\n\n"
        "**Comandos Disponibles:**\n"
        "/start - Muestra este mensaje de bienvenida y explica el funcionamiento\n"
        "/register - Registra tu cuenta para poder recibir mensajes\n"
        "/deregister - Elimina tu cuenta de los usuarios registrados\n"
    )

    # Crear el menú de teclado
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("/start", "/register", "/deregister")

    # Enviar el mensaje de bienvenida junto con el teclado
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode="Markdown")
# Handle /register command
@bot.message_handler(commands=["register"])
def register(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if username:
        # Verificar si el usuario ya está registrado
        existing_user_id = get_user_id(username)
        if existing_user_id:
            bot.reply_to(message, "You are already registered.")
        else:
            save_user(username, user_id)  # Guardar en la base de datos
            bot.reply_to(message, "You have been registered successfully!")
    else:
        bot.reply_to(message, "Please set a username in Telegram to register.")

# Handle /deregister command
@bot.message_handler(commands=["deregister"])
def deregister(message):
    username = message.from_user.username

    if username:
        # Verificar si el usuario está registrado
        existing_user_id = get_user_id(username)
        if existing_user_id:
            delete_user(username)  # Eliminar de la base de datos
            bot.reply_to(message, "You have been deregistered successfully.")
        else:
            bot.reply_to(message, "You are not registered.")
    else:
        bot.reply_to(message, "Please set a username in Telegram to use deregister.")

# Start the bot (polling)
if __name__ == "__main__":
    bot.polling()
