## TraderAI: AI-Powered Trading System

TraderAI is an open-source project that aims to develop an AI-powered trading system. It leverages artificial intelligence, machine learning, and algorithmic trading techniques to provide intelligent trading strategies, automated trade execution, and risk management capabilities.

## WARNING

This is an experimental project in development to learn to build with AI in the context of trading and financial markets.

## Key Objectives (The Plan)

Maximize Account Growth: TraderAI aims to generate consistent profits and increase the overall value of your trading account. It achieves this by identifying high-potential trading opportunities and executing trades with favorable risk-reward ratios.

Intelligent Execution: With TraderAI, trades are executed in the most optimal and intelligent manner. Market conditions, liquidity, timing, and trade execution costs are carefully considered to ensure efficient and effective execution.

Signal Analysis: TraderAI employs sophisticated algorithms and machine learning techniques to analyze and evaluate trading signals. It filters out noise and identifies the strongest signals with the highest probability of success, enhancing the accuracy and reliability of your trading decisions.

Risk Management: Protecting your trading account is a top priority for TraderAI. It incorporates robust risk management strategies, including factors such as risk-reward ratio, position sizing, stop-loss levels, and diversification, to mitigate potential losses and manage risk effectively.

Continuous Learning and Improvement: TraderAI is constantly learning and adapting to changing market conditions. It leverages historical data, market trends, and user interactions to enhance its trading strategies and algorithms, ensuring continuous improvement over time.

## Goal

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
