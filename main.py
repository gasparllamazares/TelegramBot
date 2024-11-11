from datetime import datetime
from telebot import TeleBot
import pytz
import os
from dotenv import load_dotenv
import textwrap
import requests
import google.generativeai as genai
from mqtt_client import MQTTClient  # Import MQTTClient from the new file
import json


# Load environment variables
load_dotenv()
user_state = {}
open_weather_token = os.getenv('OPEN_WEATHER_TOKEN')
telegram_api_token = os.getenv('TELEGRAM_BOT_TOKEN')
google_api_token = os.getenv('GOOGLE_API_TOKEN')
genai.configure(api_key=google_api_token)

# Set up the Telegram bot
bot = TeleBot(token=telegram_api_token)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize the reusable MQTT client
mqtt_client = MQTTClient()

spain_timezone = pytz.timezone("Europe/Madrid")


# Define bot handlers
@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(mensaje):
    hora_actual = datetime.now().strftime("%H:%M")
    fecha_actual = datetime.now().strftime("%A, %d de %B de %Y")
    prompt = (
        f"Responde como si fueras un bot de telegram llamado Brasebot, el bot de roberto brasero de antena tres noticias, estás creado por UO278137. "
        f"Da la bienvenida al usuario indicando el día {fecha_actual} y la hora tras dar los buenos días, tardes o noches dependiendo de la hora (son las {hora_actual}). "
        f"Los únicos comandos a los que respondes son /tiempo código postal, /tiempo lugar. Di una curiosidad sobre el clima. No pongas ** en el texto."
    )
    response = model.generate_content(prompt)
    generated_text = response._result.candidates[0].content.parts[0].text
    bot.reply_to(mensaje, generated_text)


@bot.message_handler(commands=['mqtt'])
def obtener_mqtt(mensaje):
    # Intentar analizar el mensaje JSON
    last_message = mqtt_client.get_last_message()
    try:
        # Analizar el mensaje JSON
        data = json.loads(last_message)
        # Convertir tiempo unix timestamp a fecha local
        timestamp = datetime.fromtimestamp(data.get('timestamp', 0), spain_timezone)

        # Extraer la información y formatearla
        formatted_message = textwrap.dedent(f"""
                
                📊 **Últimos datos obtenidos del Sensor** 📊
                🕒 Hora: {timestamp.strftime("%H:%M:%S")}
                📅 Fecha: {timestamp.strftime("%A, %d de %B de %Y")}
                🌡️ Temperatura: {data.get('temperature', 'N/A')} °C
                🌀 Presión: {data.get('pressure', 'N/A')} hPa
                
            """)
    except json.JSONDecodeError:
        # Si falla el análisis, mostrar un mensaje de error
        formatted_message = "⚠️ Error: El mensaje no está en un formato JSON válido."
    bot.reply_to(mensaje, formatted_message, parse_mode='Markdown')


# Comando para manejar /tiempo con argumentos
@bot.message_handler(commands=['tiempo'])
def handle_tiempo(mensaje):
    args = mensaje.text.split(maxsplit=1)  # Divide el comando y el argumento
    if len(args) < 2:
        # Si no hay suficientes argumentos, establece el estado y pide más información
        bot.send_message(mensaje.chat.id, "Por favor, proporciona un código postal o un nombre de lugar.")
        user_state[mensaje.chat.id] = "esperando_tiempo"
    else:
        # Si hay suficientes argumentos, procesamos el tiempo directamente
        param = args[1]
        obtener_tiempo(mensaje, param)


# Manejador para el siguiente input del usuario
@bot.message_handler(func=lambda mensaje: user_state.get(mensaje.chat.id) == "esperando_tiempo")
def obtener_segundo_argumento(mensaje):
    param = mensaje.text  # Captura el segundo argumento como ubicación
    user_state[mensaje.chat.id] = None  # Limpiar el estado del usuario después de recibir la entrada
    obtener_tiempo(mensaje, param)


# Función para obtener el tiempo de una ubicación
def obtener_tiempo(mensaje, param):
    try:
        # Crear la URL de la API según el tipo de parámetro (código postal o nombre de lugar)
        if param.isdigit():
            url = f"https://api.openweathermap.org/data/2.5/weather?zip={param},es&units=metric&appid={open_weather_token}"
        else:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={param},es&units=metric&appid={open_weather_token}"

        # Realizar la solicitud
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()

        # Obtener la hora actual en España
        current_time_in_spain = datetime.now(spain_timezone)

        # Formatear el mensaje de respuesta
        mensaje_respuesta = textwrap.dedent(f"""
            📅 Fecha: {current_time_in_spain.strftime("%A, %d de %B de %Y")}
            🕒 Hora: {current_time_in_spain.strftime("%H:%M:%S")}
            🌍 Lugar: {data['name']}
            🌡️ Temperatura: {data['main']['temp']} °C
            💧 Humedad: {data['main']['humidity']} %
            💨 Viento: {data['wind']['speed']} Km/h
            🌀 Presión: {data['main']['pressure']} hPa
            🌫️ Visibilidad: {data['visibility']} m
            🌦️ Condiciones: {data['weather'][0]['description']}
            🌅 Salida del sol: {datetime.fromtimestamp(data['sys']['sunrise'], spain_timezone).strftime("%H:%M:%S")}
            🌇 Puesta de sol: {datetime.fromtimestamp(data['sys']['sunset'], spain_timezone).strftime("%H:%M:%S")}
        """)

        bot.reply_to(mensaje, mensaje_respuesta)
    except requests.exceptions.HTTPError as http_err:
        bot.reply_to(mensaje, "No se pudo obtener el clima. Verifica el código postal o el nombre del lugar.")
        print(f"HTTP error: {http_err}")
    except Exception as err:
        bot.reply_to(mensaje, "Ocurrió un error al obtener el clima.")
        print(f"Other error: {err}")


# Ejecuta el bot


@bot.message_handler(content_types=['text'])
def respuesta_por_defecto(mensaje):
    prompt = (
        "Responde como si fueras un bot de telegram. "
        "Los únicos comandos a los que respondes son /tiempo (código postal aquí), /tiempo (un lugar aquí). "
        "Si estoy pasándote esto es porque el usuario no ha introducido un comando válido, corrígele."
    )
    response = model.generate_content(prompt)
    generated_text = response._result.candidates[0].content.parts[0].text
    bot.reply_to(mensaje, generated_text)


# Start polling
bot.infinity_polling()
