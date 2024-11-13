# Use a base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src /app/src/

# Optional: Set environment variables for certificate paths
ENV MQTT_CLIENT_CERT=/app/certs/client.crt
ENV MQTT_CLIENT_KEY=/app/certs/client.key
ENV MQTT_CA_CERT=/app/certs/ca.crt

# Run the application
CMD ["python", "/app/src/main.py"]