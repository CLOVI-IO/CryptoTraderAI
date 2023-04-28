# CryptoTraderAI

CryptoTraderAI is a Python-based project that enables automated trading on the Crypto.com Exchange using trading signals from TradingView. The project listens for incoming webhook alerts from TradingView, processes the alert data, and executes the appropriate trading actions on the Crypto.com Exchange.

## Prerequisites

Before you begin, ensure you have the following:

- A TradingView account with configured alerts for your trading strategy.
- A Crypto.com Exchange account with API access.
- Python 3.6 or higher.
- [Requests library](https://docs.python-requests.org/en/master/) for Python to handle HTTP requests.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your_username/CryptoTraderAI.git
```

2. Change to the project directory:

```bash
cd CryptoTraderAI
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the `config.example.json` file to `config.json`.

```bash
cp config.example.json config.json
```

2. Edit the `config.json` file and update it with your Crypto.com Exchange API key, API secret, and the TradingView webhook secret.

```json
{
  "crypto_com": {
    "api_key": "YOUR_CRYPTO_COM_API_KEY",
    "api_secret": "YOUR_CRYPTO_COM_API_SECRET"
  },
  "tradingview": {
    "webhook_secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET"
  }
}
```

## Running the Webhook Server

1. Start the webhook server:

```bash
python webhook_server.py
```

By default, the server listens on port 8000. You can change the port by editing the `webhook_server.py` file.

2. Configure your TradingView alerts to use the webhook URL pointing to your server. For example:

```
http://your_server_ip_or_domain:8000/webhook
```

Don't forget to include the TradingView webhook secret in the alert message if you configured one in the `config.json` file.

## Testing

You can test your webhook server by sending sample POST requests using a tool like [Postman](https://www.postman.com/) or [curl](https://curl.se/). Here's an example of a test payload:

```json
{
  "action": "buy",
  "symbol": "BTC_USDT",
  "quantity": "0.001",
  "webhook_secret": "YOUR_TRADINGVIEW_WEBHOOK_SECRET"
}
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
