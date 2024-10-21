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
mqtt_server = "95.217.41.121"
mqtt_port = 1883
mqtt_topic_publish = "/test/mssg"
client = mqtt.Client()


def connect_to_mqtt():
    try:
        client.connect(mqtt_server, mqtt_port, 60)
        print("Conectado al broker MQTT")
    except Exception as e:
        print(f"Error al conectar al broker MQTT: {e}")


model = genai.GenerativeModel('gemini-1.5-flash')

bot = TeleBot(token=telegram_api_token)

def publish_mqtt_message(message):
    try:
        connect_to_mqtt()
        result = client.publish(mqtt_topic_publish, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Mensaje publicado correctamente en {mqtt_topic_publish}")
            return True
        else:
            print("Error al publicar el mensaje en MQTT")
            return False
    except Exception as e:
        print(f"Error al intentar publicar en MQTT: {e}")
        return False


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


@bot.message_handler(commands=['mqtt'])
def enviar_mensaje_mqtt(mensaje):
    chat_id = mensaje.chat.id
    mensaje_a_enviar = mensaje.text[len('/mqtt '):].strip()

    bot.reply_to(mensaje, "Enviando mensaje a MQTT...")

    # Enviar el mensaje a MQTT
    if publish_mqtt_message(mensaje_a_enviar):
        bot.send_message(chat_id, "Mensaje enviado a MQTT exitosamente.")
    else:
        bot.send_message(chat_id, "Error al enviar el mensaje a MQTT.")


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