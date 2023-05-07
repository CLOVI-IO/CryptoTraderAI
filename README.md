# CryptoTraderAI

CryptoTraderAI is an API that receives webhook alerts from TradingView and processes them for trading automation.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have a [TradingView](https://www.tradingview.com/gopro/?share_your_love=sperreault) account with a PRO, PRO+ or PREMIUM subscription to receive alert signal (GET endpoint /webhook)

## Installation

1. Clone this repository to your local machine.
2. Install the required packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables in a `.env` file.

## Usage

To start the server, run the following command in your terminal:

```bash
uvicorn main:app --reload
```

You can then access the API at http://localhost:8000.

## Endpoints

GET /: Returns a welcome message.
GET /items/{item_id}: Returns an item by ID.
POST /webhook: Receives TradingView alerts.
GET /viewsignal: Returns the last signal received from TradingView.
