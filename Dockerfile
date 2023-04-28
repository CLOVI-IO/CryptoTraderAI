# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install the required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port on which the webhook server will listen
EXPOSE 8000

# Run the webhook server
CMD ["python", "webhook_server.py"]
