# Dockerfile

# Use a base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ /app/src/

# Copy .env.config and rename it to .env within the container
COPY .env.config /app/.env

# Run the application
CMD ["python", "/app/src/main.py"]
