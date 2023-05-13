## Prerequisites

Before you begin, ensure you have met the following requirements:

- You need a [TradingView](https://www.tradingview.com/gopro/?share_your_love=sperreault) account with a PRO, PRO+, or PREMIUM subscription to receive alert signals. The API endpoint `/webhook` will receive alerts from TradingView.

- You need a [Crypto.com Exchange](https://crypto.com/exch/ht94engn7h) account to execute trades and manage your trading account. The API endpoint `/order` will handle the order placement and management on the Crypto.com Exchange.

## Getting Started

Follow these steps to get the CryptoTraderAI up and running:

1. Clone the repository:

   ```shell
   git clone https://github.com/CLOVI-IO/CryptoTraderAI.git
   ```

2. Install the dependencies using pip:

   ```shell
   pip install -r requirements.txt
   ```

3. Set up the environment variables:

   - Create a `.env` file in the project root directory.
   - Open the `.env` file and add the necessary environment variables. Refer to the provided `.env.example` file for reference.

4. Run the application:

   ```shell
   python main.py
   ```

5. The application will start running and will be accessible at `http://localhost:8000`.

## Usage

The CryptoTraderAI API provides the following endpoints:

- `/webhook` (POST): Receives alert signals from TradingView. Make sure to set up the webhook in your TradingView account to send alerts to this endpoint.
- `/viewsignal` (GET): Retrieves the last received signal from TradingView.
- `/order` (POST): Places an order on the Crypto.com Exchange based on the last received signal.

Refer to the API documentation or the code comments for more details on the usage and input/output formats of each endpoint.

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [Contributing Guidelines](CONTRIBUTING.md) for more information.

## Support

For support or inquiries, please create an issue on the [GitHub repository](https://github.com/CLOVI-IO/CryptoTraderAI/issues).

## Acknowledgements

Special thanks to [TradingView](https://www.tradingview.com/gopro/?share_your_love=sperreault) and [Crypto.com Exchange](https://crypto.com/exch/ht94engn7h) for their services and APIs used in this project.
