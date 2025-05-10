FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY telegram_bot_mcode.py /app/
COPY google-credentials.json /app/

# Add entrypoint script
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Start the bot
ENTRYPOINT ["./entrypoint.sh"]
