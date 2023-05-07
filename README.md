# CryptoTraderAI API

This repository contains the source code for the CryptoTraderAI API. The API is built with Python, using the FastAPI and Flask frameworks. It is designed to receive and process webhook alerts from TradingView.

## Features

- Receives POST requests from TradingView alerts.
- Verifies that requests are coming from TradingView by checking the source IP address.
- Stores the latest signal received from TradingView and makes it available via a GET request.

## Installation

1. Clone this repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt` in your terminal.

## Usage

To start the API, run the following command in your terminal:

```bash
uvicorn main:app --reload
```

The API will start running at `http://localhost:8000`.

## Endpoints

- `POST /webhook`: Receives a POST request from TradingView. The request body should contain the alert data from TradingView.
- `GET /viewsignal`: Returns the latest signal received from TradingView.

## Deployment

This API is designed to be deployed on AWS Elastic Beanstalk. You can use the included `go.sh` script to automatically add, commit, and push your changes to GitHub, and then deploy them to Elastic Beanstalk. To use the script, simply type `go` in your terminal.

```bash
go
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
