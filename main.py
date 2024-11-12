from datetime import datetime
from telebot import TeleBot, types
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
@bot.message_handler(commands=['start'])
def mostrar_menu(mensaje):
    # Crear el menú con botones para cada comando
    menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    boton_tiempo = types.KeyboardButton('/tiempo')
    boton_calidad_aire = types.KeyboardButton('/calidad_aire')
    boton_promedio_temp = types.KeyboardButton('/promedio_temp')
    boton_prediccion_general = types.KeyboardButton('/prediccion_general')
    boton_mqtt = types.KeyboardButton('/mqtt')
    boton_help = types.KeyboardButton('/help')

    # Agregar los botones al menú
    menu.add(boton_tiempo, boton_calidad_aire, boton_promedio_temp, boton_prediccion_general, boton_mqtt, boton_help)

    # Enviar el menú como respuesta al comando /start
    bot.send_message(mensaje.chat.id, "Selecciona una opción:", reply_markup=menu)

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
                
                📊 **Últimos datos obtenidos del Sensor** 
                🕒 Hora: {timestamp.strftime("%H:%M:%S")}
                📅 Fecha: {timestamp.strftime("%d/%m/%Y")}
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
            📅 Fecha: {current_time_in_spain.strftime("%d/%m/%Y")}
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

@bot.message_handler(commands=['calidad_aire'])
def handle_calidad_aire(mensaje):
    args = mensaje.text.split(maxsplit=1)  # Divide el comando y el argumento
    if len(args) < 2:
        # Si no hay suficientes argumentos, establece el estado y pide más información
        bot.send_message(mensaje.chat.id, "Por favor, proporciona un código postal o un nombre de lugar para la calidad del aire.")
        user_state[mensaje.chat.id] = "esperando_calidad_aire"
    else:
        # Si hay suficientes argumentos, procesamos la calidad del aire directamente
        param = args[1]
        obtener_calidad_aire(mensaje, param)

# Manejador para el siguiente input del usuario si falta el parámetro
@bot.message_handler(func=lambda mensaje: user_state.get(mensaje.chat.id) == "esperando_calidad_aire")
def obtener_segundo_argumento_calidad_aire(mensaje):
    param = mensaje.text  # Captura el segundo argumento como ubicación
    user_state[mensaje.chat.id] = None  # Limpiar el estado del usuario después de recibir la entrada
    obtener_calidad_aire(mensaje, param)

# Función para obtener calidad del aire de una ubicación
def obtener_calidad_aire(mensaje, param):
    try:
        # Determina si `param` es un código postal (solo dígitos) o una ciudad
        if param.isdigit():
            # URL para obtener lat y lon usando código postal
            geocode_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={param},es&appid={open_weather_token}"
        else:
            # URL para obtener lat y lon usando nombre de ciudad
            geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={param},es&limit=1&appid={open_weather_token}"

        # Realizar la solicitud para obtener las coordenadas
        geocode_res = requests.get(geocode_url)
        geocode_res.raise_for_status()
        geocode_data = geocode_res.json()

        # Procesar los datos de coordenadas
        if param.isdigit():
            # La respuesta es un solo diccionario cuando se usa el endpoint /zip
            lat = geocode_data['lat']
            lon = geocode_data['lon']
        elif geocode_data:
            # La respuesta es una lista cuando se usa el endpoint /direct
            lat = geocode_data[0]['lat']
            lon = geocode_data[0]['lon']
        else:
            bot.send_message(mensaje.chat.id, "No se pudo encontrar la ubicación especificada.")
            return

        # Obtener calidad del aire con latitud y longitud
        air_quality_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={open_weather_token}"
        air_quality_res = requests.get(air_quality_url)
        air_quality_res.raise_for_status()
        air_quality_data = air_quality_res.json()

        # Extraer el índice de calidad del aire
        air_quality_index = air_quality_data['list'][0]['main']['aqi']

        # Traducir el índice de calidad del aire al texto con emojis
        calidad_aire_texto = {

            1: "Buena (🟢)",
            2: "Razonable (🟡)",
            3: "Regular (🟠)",
            4: "Pobre (🔴)",
            5: "Muy pobre (🟣)"
        }
        calidad_aire = calidad_aire_texto.get(air_quality_index, "Desconocida")

        # Obtener la hora actual en España
        current_time_in_spain = datetime.now(spain_timezone)

        # Formatear el mensaje de respuesta
        mensaje_respuesta = textwrap.dedent(f"""
            📅 Fecha: {current_time_in_spain.strftime("%d/%m/%Y")}
            🕒 Hora: {current_time_in_spain.strftime("%H:%M:%S")}
            🌍 Lugar: {param.capitalize()}
            
            💨 Calidad del Aire: {calidad_aire} (Índice: {air_quality_index})
        """)

        bot.reply_to(mensaje, mensaje_respuesta.strip())
    except requests.exceptions.HTTPError as http_err:
        bot.reply_to(mensaje, "No se pudo obtener la calidad del aire. Verifica el código postal o el nombre del lugar.")
        print(f"HTTP error: {http_err}")
    except Exception as err:
        bot.reply_to(mensaje, "Ocurrió un error al obtener la calidad del aire.")
        print(f"Other error: {err}")


@bot.message_handler(commands=['promedio_temp'])
def handle_promedio_temp(mensaje):
    args = mensaje.text.split(maxsplit=1)  # Divide el comando y el argumento
    if len(args) < 2:
        # Si no hay suficientes argumentos, establece el estado y pide más información
        bot.send_message(mensaje.chat.id, "Por favor, proporciona un código postal o un nombre de lugar para el cálculo del promedio de temperatura.")
        user_state[mensaje.chat.id] = "esperando_promedio_temp"
    else:
        # Si hay suficientes argumentos, procesamos el promedio de temperatura directamente
        param = args[1]
        obtener_promedio_temp(mensaje, param)

# Manejador para el siguiente input del usuario si falta el parámetro
@bot.message_handler(func=lambda mensaje: user_state.get(mensaje.chat.id) == "esperando_promedio_temp")
def obtener_segundo_argumento_promedio_temp(mensaje):
    param = mensaje.text  # Captura el segundo argumento como ubicación
    user_state[mensaje.chat.id] = None  # Limpiar el estado del usuario después de recibir la entrada
    obtener_promedio_temp(mensaje, param)

# Función para obtener el promedio de temperatura de una ubicación
def obtener_promedio_temp(mensaje, param):
    try:
        # Determina si `param` es un código postal (solo dígitos) o una ciudad
        if param.isdigit():
            # URL para obtener lat y lon usando código postal
            geocode_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={param},es&appid={open_weather_token}"
        else:
            # URL para obtener lat y lon usando nombre de ciudad
            geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={param},es&limit=1&appid={open_weather_token}"

        # Realizar la solicitud para obtener las coordenadas
        geocode_res = requests.get(geocode_url)
        geocode_res.raise_for_status()
        geocode_data = geocode_res.json()

        # Procesar los datos de coordenadas
        if param.isdigit():
            lat = geocode_data['lat']
            lon = geocode_data['lon']
        elif geocode_data:
            lat = geocode_data[0]['lat']
            lon = geocode_data[0]['lon']
        else:
            bot.send_message(mensaje.chat.id, "No se pudo encontrar la ubicación especificada.")
            return

        # Obtener el pronóstico de temperatura para los próximos 5 días
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={open_weather_token}"
        forecast_res = requests.get(forecast_url)
        forecast_res.raise_for_status()
        forecast_data = forecast_res.json()

        # Calcular el promedio de temperatura
        temperaturas = [entry['main']['temp'] for entry in forecast_data['list']]
        promedio_temp = sum(temperaturas) / len(temperaturas)

        # Obtener la hora actual en España
        current_time_in_spain = datetime.now(spain_timezone)

        # Formatear el mensaje de respuesta
        mensaje_respuesta = textwrap.dedent(f"""
            📅 Fecha: {current_time_in_spain.strftime("%d/%m/%Y")}
            🕒 Hora: {current_time_in_spain.strftime("%H:%M:%S")}
            
            🌍 Lugar: {param.capitalize()}
            🌡️ Temperatura Promedio Próximos 5 Días: {promedio_temp:.2f} °C
        """)

        bot.reply_to(mensaje, mensaje_respuesta.strip())
    except requests.exceptions.HTTPError as http_err:
        bot.reply_to(mensaje, "No se pudo obtener el promedio de la temperatura. Verifica el código postal o el nombre del lugar.")
        print(f"HTTP error: {http_err}")
    except Exception as err:
        bot.reply_to(mensaje, "Ocurrió un error al obtener el promedio de la temperatura.")
        print(f"Other error: {err}")



# Función para enviar los datos de pronóstico a Gemini y obtener la predicción
def obtener_prediccion_gemini(forecast_res):
    # Convertir los datos JSON en una cadena de texto
    forecast_data = json.dumps(forecast_res)

    # Crear el prompt para la predicción
    prompt = (
            "A continuación, tienes un conjunto de datos meteorológicos en formato JSON. "
            "Por favor, realiza una predicción general del tiempo basado en estos datos para los próximos días.\n\n"
            "Datos meteorológicos JSON:\n" + forecast_data +"Envia la respuesta en formato MARKDOWNV2."
    )

    # Llamar a la API de Gemini para obtener la respuesta
    try:
        response = model.generate_content(prompt)
        # Obtener el texto generado
        prediccion = response._result.candidates[0].content.parts[0].text
        return prediccion
    except Exception as e:
        print(f"Error al generar predicción con Gemini: {e}")
        return "Ocurrió un error al intentar realizar la predicción del tiempo."




# Comando para manejar /prediccion_general
@bot.message_handler(commands=['prediccion_general'])
def handle_prediccion_general(mensaje):
    args = mensaje.text.split(maxsplit=1)  # Divide el comando y el argumento
    if len(args) < 2:
        # Si no hay suficientes argumentos, establece el estado y pide más información
        bot.send_message(mensaje.chat.id,
                         "Por favor, proporciona un código postal o un nombre de lugar para la predicción del tiempo.")
        user_state[mensaje.chat.id] = "esperando_prediccion_general"
    else:
        # Si hay suficientes argumentos, procesamos la predicción directamente
        param = args[1]
        obtener_prediccion_general(mensaje, param)


# Manejador para el siguiente input del usuario si falta el parámetro
@bot.message_handler(func=lambda mensaje: user_state.get(mensaje.chat.id) == "esperando_prediccion_general")
def obtener_segundo_argumento_prediccion_general(mensaje):
    param = mensaje.text  # Captura el segundo argumento como ubicación
    user_state[mensaje.chat.id] = None  # Limpiar el estado del usuario después de recibir la entrada
    obtener_prediccion_general(mensaje, param)

# Función para obtener predicción de tiempo de una ubicación
def obtener_prediccion_general(mensaje, param):
    try:
        # Determina si `param` es un código postal (solo dígitos) o una ciudad
        if param.isdigit():
            # URL para obtener lat y lon usando código postal
            geocode_url = f"http://api.openweathermap.org/geo/1.0/zip?zip={param},es&appid={open_weather_token}"
        else:
            # URL para obtener lat y lon usando nombre de ciudad
            geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={param},es&limit=1&appid={open_weather_token}"

        # Realizar la solicitud para obtener las coordenadas
        geocode_res = requests.get(geocode_url)
        geocode_res.raise_for_status()
        geocode_data = geocode_res.json()

        # Procesar los datos de coordenadas
        if param.isdigit():
            lat = geocode_data['lat']
            lon = geocode_data['lon']
        elif geocode_data:
            lat = geocode_data[0]['lat']
            lon = geocode_data[0]['lon']
        else:
            bot.send_message(mensaje.chat.id, "No se pudo encontrar la ubicación especificada.")
            return

        # Obtener el pronóstico de temperatura para los próximos 5 días
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={open_weather_token}"
        forecast_res = requests.get(forecast_url)
        forecast_res.raise_for_status()
        forecast_data = forecast_res.json()

        # Enviar los datos a Gemini para obtener la predicción
        prediccion = obtener_prediccion_gemini(forecast_data)

        # Obtener la hora actual en España
        current_time_in_spain = datetime.now(spain_timezone)

        # Formatear el mensaje de respuesta
        mensaje_respuesta = textwrap.dedent(f"""📅 Fecha: {current_time_in_spain.strftime("%d/%m/%Y")}
🕒 Hora: {current_time_in_spain.strftime("%H:%M:%S")}

🌍 Lugar: {param.capitalize()}
🔮 Predicción General del Tiempo: 

{prediccion}
        """)

        bot.reply_to(mensaje, mensaje_respuesta.strip())
    except requests.exceptions.HTTPError as http_err:
        bot.reply_to(mensaje,
                     "No se pudo obtener los datos de pronóstico. Verifica el código postal o el nombre del lugar.")
        print(f"HTTP error: {http_err}")
    except Exception as err:
        bot.reply_to(mensaje, "Ocurrió un error al obtener la predicción general del tiempo.", parse_mode='MarkdownV2')
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
