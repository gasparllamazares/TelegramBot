from telebot import TeleBot
import os
from dotenv import load_dotenv
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown


load_dotenv()

open_weather_token = os.getenv('OPEN_WEATHER_TOKEN')
telegram_api_token = os.getenv('TELEGRAM_BOT_TOKEN')
google_api_token = os.getenv('GOOGLE_API_TOKEN')  # La clave API para Google Generative AI
genai.configure(api_key=google_api_token)


def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

model = genai.GenerativeModel('gemini-1.5-flash')

bot = TeleBot(token=telegram_api_token)

@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(mensaje):
    bot.reply_to(mensaje, 'Hola, soy botardo.')


@bot.message_handler(content_types=['text'])
def respuesta_por_defecto(mensaje):
    # Ajustar el prompt para que el modelo responda como si fuera el bot
    prompt = f"Responde como si fueras un bot de telegram llamado Botardo, estás creado por UO278137,\
     tu funcion es dar detalles sobre el tiempo por comandos, si estás recibiendo este mensaje es porque el usuario está \
     escribiendo algo para lo que el bot no está programado. Los únicos comandos a los que respondes son\
      /tiempo código postal, /tiempo lugar. \n El usuario dice: {mensaje.text}"

    # Generar respuesta usando el modelo
    response = model.generate_content(prompt)

    # Extraer solo el texto generado
    generated_text = response._result.candidates[0].content.parts[0].text

    # Enviar la respuesta al usuario
    bot.reply_to(mensaje, generated_text)


bot.infinity_polling()