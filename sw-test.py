import websocket

try:
    # Replace with your websocket url
    websocket_url = "wss://stream.crypto.com/v2/user"

    # Create a new WebSocket connection
    ws = websocket.create_connection(websocket_url)

    print("Connecting to {} ...".format(websocket_url))

    # Send a small message
    ws.send("Hello, WebSocket!")

    # Receive and print the response
    result = ws.recv()
    print("Received: '{}'".format(result))

    # Close the connection
    ws.close()

except Exception as e:
    print("Caught exception: " + str(e))
