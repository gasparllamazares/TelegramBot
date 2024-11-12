import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import time
# Load environment variables for MQTT credentials and server details
load_dotenv()

mqtt_server = "mqtt.gaspi.es"
mqtt_port = 8883
mqtt_topic = "/ESP32-1/bmp280/data"
mqtt_client_cert = os.getenv('MQTT_CLIENT_CERT')
mqtt_client_key = os.getenv('MQTT_CLIENT_KEY')
mqtt_ca_cert = os.getenv('MQTT_CA_CERT')

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.configure_tls()
        self.last_message = None

    def configure_tls(self):
        # Set up TLS/SSL with client certificate and key
        self.client.tls_set(
            ca_certs=mqtt_ca_cert,
            certfile=mqtt_client_cert,
            keyfile=mqtt_client_key
        )

    def connect(self):
        try:
            self.client.connect(mqtt_server, mqtt_port)
            self.client.on_message = self.on_message
            self.client.loop_start()
        except Exception as e:
            print(f"Error connecting to MQTT server: {e}")

    def on_message(self, client, userdata, message):
        # Handle the last message and store it in `last_message`
        self.last_message = message.payload.decode("utf-8")

    def get_last_message(self):
        # Connect and subscribe to the topic
        self.connect()
        self.client.subscribe(mqtt_topic)

        # Wait a brief moment to allow retained message to be received
        time.sleep(1)

        # Stop the loop and disconnect
        self.client.loop_stop()
        self.client.disconnect()

        # Return the last received message or an error message
        return self.last_message or "No retained message available."
