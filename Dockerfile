FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot files
COPY telegram_bot_mcode.py /app/
COPY entrypoint.sh /app/

# Give execute permission to entrypoint script
RUN chmod +x /app/entrypoint.sh

# Run entrypoint
ENTRYPOINT ["./entrypoint.sh"]
