from datetime import datetime
from telebot import TeleBot
import os
from dotenv import load_dotenv
import textwrap
import requests
import google.generativeai as genai
from mqtt_client import MQTTClient  # Import MQTTClient from the new file
import json


# Load environment variables
load_dotenv()

open_weather_token = os.getenv('OPEN_WEATHER_TOKEN')
telegram_api_token = os.getenv('TELEGRAM_BOT_TOKEN')
google_api_token = os.getenv('GOOGLE_API_TOKEN')
genai.configure(api_key=google_api_token)

# Set up the Telegram bot
bot = TeleBot(token=telegram_api_token)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize the reusable MQTT client
mqtt_client = MQTTClient()


# Define bot handlers
@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(mensaje):
    hora_actual = datetime.now().strftime("%H:%M")
    fecha_actual = datetime.now().strftime("%A, %d de %B de %Y")
    prompt = (
        f"Responde como si fueras un bot de telegram llamado Brasebot, el bot de roberto brasero de antena tres noticias, estás creado por UO278137. "
        f"Da la bienvenida al usuario indicando el día {fecha_actual} y la hora tras dar los buenos días, tardes o noches dependiendo de la hora (son las {hora_actual}). "
        f"Los únicos comandos a los que respondes son /tiempo código postal, /tiempo lugar."
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

        # Extraer la información y formatearla
        formatted_message = textwrap.dedent(f"""
                📊 **Últimos datos obtenidos del Sensor** 📊
                🌡️ Temperatura: {data.get('temperature', 'N/A')} °C
                💨 Presión: {data.get('pressure', 'N/A')} hPa
                🕒 Hora UTC: {data.get('timestamp', 'N/A')}
            """)
    except json.JSONDecodeError:
        # Si falla el análisis, mostrar un mensaje de error
        formatted_message = "⚠️ Error: El mensaje no está en un formato JSON válido."
    bot.reply_to(mensaje, formatted_message, parse_mode='Markdown')


@bot.message_handler(commands=['tiempo'])
def obtener_tiempo(mensaje):
    param = ' '.join(mensaje.text.split()[1:])
    if not param:
        bot.reply_to(mensaje, "Por favor, proporciona un código postal o un nombre de lugar.")
        return
    try:
        if param.isdigit():
            url = f"https://api.openweathermap.org/data/2.5/weather?zip={param},es&units=metric&appid={open_weather_token}"
        else:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={param},es&units=metric&appid={open_weather_token}"

        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #con emojis
        mensaje_respuesta = textwrap.dedent(f"""
            📅 Fecha y hora UTC
                {fecha_hora}
            🌍 Lugar: {data['name']}
            🌡️ Temperatura: {data['main']['temp']} °C
            💧 Humedad: {data['main']['humidity']} %
            💨 Viento: {data['wind']['speed']} Km/h
            🌇 Puesta de sol: {datetime.fromtimestamp(data['sys']['sunset']).strftime("%H:%M:%S")}
        
        """)
        bot.reply_to(mensaje, mensaje_respuesta)
    except requests.exceptions.HTTPError as http_err:
        bot.reply_to(mensaje, "No se pudo obtener el clima. Verifica el código postal o el nombre del lugar.")
        print(f"HTTP error: {http_err}")
    except Exception as err:
        bot.reply_to(mensaje, "Ocurrió un error al obtener el clima.")
        print(f"Other error: {err}")


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
