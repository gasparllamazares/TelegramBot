# Dockerfile

# Use a base image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src /app/src/

# Set up the command to run both bot.py and main.py
CMD ["sh", "-c", "python /app/src/bot.py & python /app/src/main.py"]