import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from routes import webhook, viewsignal, order, exchange, last_order
from exchanges.crypto_com.private import user_balance_ws
from exchanges.crypto_com.public.auth import get_auth
from models import Payload
from redis_handler import RedisHandler
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Middleware to add ngrok-skip-browser-warning header
@app.middleware("http")
async def add_ngrok_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# Initialize last_signal in the application state
app.state.last_signal = None

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Log the environment variables being used
logging.info(f"REDIS_HOST: {REDIS_HOST}")
logging.info(f"REDIS_PORT: {REDIS_PORT}")
logging.info(f"REDIS_PASSWORD: {'******' if REDIS_PASSWORD else 'None'}")
logging.info(f"REDIS_DB: {REDIS_DB}")

# Create RedisHandler instance and subscribe to the Redis channel 'last_signal'
redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)
redis_client = redis_handler.redis_client
pubsub = redis_client.pubsub()
pubsub.subscribe("last_signal")
logging.info("Order: Subscribed to 'last_signal' channel")

# Add a task that runs in the background after startup
@app.on_event("startup")
async def startup_event():
    async def listen_to_redis():
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_signal = Payload(**json.loads(message["data"]))
                logging.info(
                    f"Order: Received last_signal from Redis channel: {last_signal}"
                )
                app.state.last_signal = (
                    last_signal  # update last_signal in the app state
                )
            await asyncio.sleep(0.1)

    async def start_user_balance_subscription():
        auth = get_auth()  # Ensure get_auth is called correctly without awaiting
        await user_balance_ws.fetch_user_balance(auth)

    loop = asyncio.get_event_loop()
    loop.create_task(listen_to_redis())
    loop.create_task(start_user_balance_subscription())

@app.get("/")
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Dashboard</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 0;
                    color: #333;
                }
                .container {
                    max-width: 1200px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #fff;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                }
                .header h1 {
                    color: #333;
                }
                .metric {
                    display: inline-block;
                    width: 30%;
                    margin: 1%;
                    padding: 20px;
                    background: #e0e0e0;
                    border-radius: 8px;
                    color: #333;
                    text-align: center;
                }
                .metric h2 {
                    margin: 0;
                    font-size: 2em;
                }
                .metric p {
                    margin: 10px 0 0;
                    font-size: 1.2em;
                }
                .list {
                    margin-top: 20px;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                }
                li {
                    background: #e0e0e0;
                    margin: 0.5em 0;
                    padding: 0.5em;
                    border-radius: 5px;
                    color: #333;
                    text-align: center;
                }
                .chart-container {
                    position: relative;
                    margin: 0 auto;
                    height: 400px;
                    width: 80%;
                }
            </style>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Dashboard</h1>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <h2 id="metric1">0</h2>
                        <p>Active Subscriptions</p>
                    </div>
                    <div class="metric">
                        <h2 id="metric2">0</h2>
                        <p>Processed Signals</p>
                    </div>
                    <div class="metric">
                        <h2 id="metric3">0</h2>
                        <p>Last Signal</p>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="myChart"></canvas>
                </div>
                <div class="list">
                    <h2>WebSocket Subscriptions</h2>
                    <ul id="subscriptions">
                        <!-- Subscriptions will be populated here -->
                    </ul>
                </div>
            </div>
            <script>
                async function fetchMetrics() {
                    const response = await fetch('/subscriptions');
                    const data = await response.json();
                    document.getElementById('metric1').textContent = data.subscriptions.length;

                    const subscriptionsList = document.getElementById('subscriptions');
                    subscriptionsList.innerHTML = '';
                    data.subscriptions.forEach(sub => {
                        const li = document.createElement('li');
                        li.textContent = sub;
                        subscriptionsList.appendChild(li);
                    });

                    const lastSignalResponse = await fetch('/last_signal');
                    const lastSignalData = await lastSignalResponse.json();
                    document.getElementById('metric3').textContent = lastSignalData.last_signal ? lastSignalData.last_signal.id : 'N/A';
                }

                async function fetchChartData() {
                    // Fetch the data for the chart (replace with actual data fetching)
                    const response = await fetch('/chart_data');
                    const data = await response.json();
                    return data;
                }

                function createChart(data) {
                    const ctx = document.getElementById('myChart').getContext('2d');
                    const myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'Total Balance',
                                data: data.values,
                                backgroundColor: 'rgba(26, 188, 156, 0.2)',
                                borderColor: 'rgba(26, 188, 156, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                }

                // Fetch metrics and chart data on page load
                window.onload = async () => {
                    fetchMetrics();
                    const chartData = await fetchChartData();
                    createChart(chartData);
                };

                // Fetch metrics every 5 seconds
                setInterval(fetchMetrics, 5000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/subscriptions")
async def get_subscriptions():
    return {"subscriptions": list(user_balance_ws.connected_websockets)}

@app.get("/last_signal")
async def get_last_signal():
    last_signal = app.state.last_signal
    return {"last_signal": last_signal.dict() if last_signal else None}

@app.get("/chart_data")
async def get_chart_data():
    # Fetch data from Redis or other storage
    user_balance_redis = redis_handler.redis_client.get("user_balance")
    if user_balance_redis:
        balance_data = json.loads(user_balance_redis)
        # Extract and process balance data for chart
        labels = [entry['currency'] for entry in balance_data['result']['data']]
        values = [entry['balance'] for entry in balance_data['result']['data']]
        data = {"labels": labels, "values": values}
    else:
        data = {"labels": [], "values": []}  # Handle no data case
    return data

# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)

if __name__ == "__main__":
    import uvicorn

    logging.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
