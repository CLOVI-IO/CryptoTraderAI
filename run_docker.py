import os
import docker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
crypto_com_api_key = os.getenv("CRYPTO_COM_API_KEY")
crypto_com_api_secret = os.getenv("CRYPTO_COM_API_SECRET")
tradingview_webhook_secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")

# Initialize Docker client
client = docker.from_env()

# Build Docker image
print("Building Docker image...")
image, _ = client.images.build(path=".", tag="cryptotraderai", rm=True)
print("Docker image built successfully.")

# Run Docker container
print("Running Docker container...")
container = client.containers.run(
    image=image.id,
    name="cryptotraderai",
    ports={"8000/tcp": 8000},
    environment={
        "CRYPTO_COM_API_KEY": crypto_com_api_key,
        "CRYPTO_COM_API_SECRET": crypto_com_api_secret,
        "TRADINGVIEW_WEBHOOK_SECRET": tradingview_webhook_secret,
    },
    detach=True,
)
print(f"Docker container running. ID: {container.id}")
