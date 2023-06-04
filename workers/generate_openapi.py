import importlib
import json
import sys
from typing import List
from fastapi import FastAPI
from fastapi.routing import APIRoute, APIWebSocketRoute

app_name = (
    sys.argv[1]
    if len(sys.argv) > 1
    else input("Enter the name of your FastAPI application: ")
)


def get_app_endpoints(app_module):
    http_endpoints = [
        route for route in app_module.app.routes if isinstance(route, APIRoute)
    ]
    ws_endpoints = [
        route for route in app_module.app.routes if isinstance(route, APIWebSocketRoute)
    ]
    return http_endpoints, ws_endpoints


def generate_openapi_spec(
    app_name: str,
    app_module,
    http_endpoints: List[APIRoute],
    ws_endpoints: List[APIWebSocketRoute],
) -> dict:
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": app_name,
            "version": "1.0.0",
        },
        "paths": {},
    }

    # Add more details for HTTP endpoints
    for route in http_endpoints:
        openapi_spec["paths"][route.path] = {
            method.lower(): {
                "summary": f"Enter summary for {method} {route.path}",
                "description": f"Enter description for {method} {route.path}",
                "responses": {"200": {"description": "Successful Response"}},
            }
            for method in route.methods
        }

    # Add more details for WebSocket endpoints
    for route in ws_endpoints:
        openapi_spec["paths"][route.path] = {
            "get": {
                "summary": f"Enter summary for WebSocket endpoint {route.path}",
                "description": f"Enter description for WebSocket endpoint {route.path}",
                "responses": {"200": {"description": "Successful Connection"}},
            }
        }

    return openapi_spec


def main():
    try:
        app_module = importlib.import_module(app_name)
    except ImportError:
        print(
            f"Couldn't import {app_name}. Make sure you're running this script in the right context."
        )
        return

    http_endpoints, ws_endpoints = get_app_endpoints(app_module)
    openapi_spec = generate_openapi_spec(
        app_name, app_module, http_endpoints, ws_endpoints
    )

    with open("openapi_template.json", "w") as outfile:
        json.dump(openapi_spec, outfile, indent=4)


if __name__ == "__main__":
    main()
