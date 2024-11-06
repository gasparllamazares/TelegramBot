from telebot import TeleBot
import os
from dotenv import load_dotenv
import pathlib
import textwrap
import requests, json
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown
import paho.mqtt.client as mqtt


load_dotenv()

open_weather_token = os.getenv('OPEN_WEATHER_TOKEN')
telegram_api_token = os.getenv('TELEGRAM_BOT_TOKEN')
google_api_token = os.getenv('GOOGLE_API_TOKEN')  # La clave API para Google Generative AI
genai.configure(api_key=google_api_token)

telegram_api_token = os.getenv('TELEGRAM_BOT_TOKEN')
mqtt_server = "mqtt.gaspi.es"
mqtt_port = 1883
client = mqtt.Client()

model = genai.GenerativeModel('gemini-1.5-flash')

bot = TeleBot(token=telegram_api_token)




@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(mensaje):
    # Ajustar el prompt para que el modelo responda como si fuera el bot
    prompt = f"Responde como si fueras un bot de telegram llamado Botardo, estás creado por UO278137,\
         tu funcion es dar detalles sobre el tiempo por comandos, si estás recibiendo este mensaje es porque el usuario está \
         escribiendo algo para lo que el bot no está programado. Los únicos comandos a los que respondes son\
          /tiempo código postal, /tiempo lugar. Da una bienvenida al usuario, vas a responder al comando start\n"

    # Generar respuesta usando el modelo
    response = model.generate_content(prompt)

    # Extraer solo el texto generado
    generated_text = response._result.candidates[0].content.parts[0].text

    # Enviar la respuesta al usuario
    bot.reply_to(mensaje, generated_text)

# Callback para recibir mensajes de MQTT
def on_message(client, userdata, message):
    # Asigna el payload del mensaje recibido
    mqtt_message = message.payload.decode("utf-8")
    # Envía el mensaje al usuario que solicitó el comando
    bot.reply_to(userdata['message'], mqtt_message)
    client.loop_stop()
@bot.message_handler(commands=['mqtt'])

def mqtt_obtener_temperatura(mensaje):
    # Conectarse al servidor mqtt
    client.user_data_set({'message': mensaje})  # Guarda el mensaje original
    client.on_message = on_message  # Configura el callback para mensajes
    client.connect(mqtt_server, mqtt_port)

    # Suscribirse al tópico
    client.subscribe("/ESP32/temperatura")
    # Indicar al usuario que se está esperando por la temperatura
    bot.reply_to(mensaje, "Esperando por la temperatura...")
    client.loop_start()  # Inicia el bucle para escuchar mensajes










@bot.message_handler(commands=['tiempo'])
def obtener_tiempo(mensaje):
    # Extraer el parámetro del mensaje después del comando
    param = ' '.join(mensaje.text.split()[1:])

    # Verificar si se ingresó un parámetro
    if not param:
        bot.reply_to(mensaje, "Por favor, proporciona un código postal o un nombre de lugar.")
        return
    # Intentar tratar el parámetro como un código postal
    try:
        CP = int(param)
        url = f"https://api.openweathermap.org/data/2.5/weather?zip={CP},es&units=metric&appid={open_weather_token}"
    except ValueError:
        # Si no es un código postal, tratarlo como un nombre de lugar
        lugar = param
        url = f"https://api.openweathermap.org/data/2.5/weather?q={lugar},es&units=metric&appid={open_weather_token}"

    # Realizar la solicitud a la API
    try:
        res = requests.get(url)
        res.raise_for_status()  # Lanza una excepción si la respuesta tiene un error
        data = res.json()

        # Enviar el nombre de la ciudad y la temperatura al usuario
        bot.reply_to(mensaje, f"El clima en {data['name']} es de {data['main']['temp']}°C.")
    except requests.exceptions.HTTPError as http_err:
        bot.reply_to(mensaje, "No se pudo obtener el clima. Verifica el código postal o el nombre del lugar.")
        print(f"HTTP error: {http_err}")
    except Exception as err:
        bot.reply_to(mensaje, "Ocurrió un error al obtener el clima.")
        print(f"Other error: {err}")


@bot.message_handler(content_types=['text'])
def respuesta_por_defecto(mensaje):
    # Ajustar el prompt para que el modelo responda como si fuera el bot
    prompt = f"Responde como si fueras un bot de telegram,\
     tu funcion es dar detalles sobre el tiempo por comandos, si estás recibiendo este mensaje es porque el usuario está \
     escribiendo algo para lo que el bot no está programado, eres el último message handler. Los únicos comandos a los que respondes son\
      /tiempo (código postal aquí), /tiempo (un lugar aquí). Si estoy pasandote esto es porque el usuario no ha introducido un comando válido, corrígele\n"


    # Generar respuesta usando el modelo
    response = model.generate_content(prompt)

    # Extraer solo el texto generado
    generated_text = response._result.candidates[0].content.parts[0].text

    # Enviar la respuesta al usuario
    bot.reply_to(mensaje, generated_text)


bot.infinity_polling()