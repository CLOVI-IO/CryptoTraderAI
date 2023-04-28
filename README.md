# CryptoTraderAI

CryptoTraderAI is a Python-based project that automates trading on the Crypto.com Exchange using TradingView signals. It listens for incoming webhook alerts from TradingView, processes the alert data, and executes appropriate trading actions on the Crypto.com Exchange.

This guide shows you how to configure, build, and run CryptoTraderAI in a Docker container.

## Prerequisites

- Docker installed on your machine (https://www.docker.com/)
- TradingView account with configured alerts for your trading strategy
- Crypto.com Exchange account with API access
- Python 3.10 or higher

## Setup

1. Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/cboseb/CryptoTraderAI.git
cd CryptoTraderAI
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Crypto.com Exchange API key, API secret, and TradingView webhook secret:

```ini
CRYPTO_COM_API_KEY=YOUR_CRYPTO_COM_API_KEY
CRYPTO_COM_API_SECRET=YOUR_CRYPTO_COM_API_SECRET
TRADINGVIEW_WEBHOOK_SECRET=YOUR_TRADINGVIEW_WEBHOOK_SECRET
```

4. Build and run the Docker container:

```bash
python run_docker.py
```

The CryptoTraderAI webhook server will run in a Docker container on port 8000.

5. Configure your TradingView alerts to use the webhook URL pointing to your server:

```
http://your_server_ip_or_domain:8000/webhook
```

Include the TradingView webhook secret in the alert message if you configured one in the `.env` file.
