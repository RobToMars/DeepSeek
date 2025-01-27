# fake_ollama_server.py
# -*- coding: UTF-8 -*-

""" Fake Ollama Server for testing Ollama integration with Deepseek for PyCharm IDE """

# Built-in Python libraries
import os
import json
import logging
import time

# External Python libraries
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import requests
import uvicorn

# Package Python libraries

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
app = FastAPI()
start_time = time.time()

OLLAMA_ADDRESS = os.getenv("OLLAMA_ADDRESS", "127.0.0.1")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))

API_URL = os.getenv("API_URL", "https://api.deepseek.com/v1/chat/completions")
API_KEY = os.getenv("API_KEY")  # Retrieve the API key from the environment variable
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

MODEL_CHAT = "deepseek-chat"
MODEL_CODER = "deepseek-coder"
MODEL_REASONER = "deepseek-reasoner"
MODEL_METADATA = {
    "modified_at": "2024-03-15T10:00:00Z",
    "size": 12000000000,
    "digest": "abcde12345fghij67890klmno1234567890abcdef",
    "details": {
        "parent_model": "deepseek-base",
        "format": "gguf",
        "family": "deepseek",
        "families": ["deepseek"],
    },
}

JSON_MEDIA_TYPE = "application/json"
DONE_MARKER = b"data: [DONE]"
DATA_PREFIX = b"data: "


@app.get("/")
async def root():
    """
    Handles the root endpoint of the application.

    This function is mapped to the root endpoint ("/") of the application
    and returns a JSON response containing a message indicating that
    Ollama is running. It utilizes FastAPI's asynchronous support for
    handling HTTP requests and relies on the `JSONResponse` class for
    sending structured JSON data as the HTTP response.

    Returns
    -------
    JSONResponse
        An instance of FastAPI's JSONResponse containing the message
        indicating the application is operational.
    """
    return JSONResponse(content={"message": "Ollama is running"})


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring server status.

    Returns
    -------
    JSONResponse
        Status information including server health and model availability.
    """
    return JSONResponse(content={
        "status": "healthy",
        "models": [MODEL_CHAT, MODEL_REASONER],
        "uptime": time.time() - start_time
    })


# Add this validation function
def validate_message_sequence(messages, model):
    """Validate message sequence alternates between user/assistant roles."""
    if model != MODEL_REASONER:
        return  # Only enforce for reasoner model

    if not messages:
        return {"error": "Empty message list", "code": "invalid_messages"}

    # First message must be from user
    if messages[0]["role"] != "user":
        return {"error": "First message must be from user", "code": "invalid_first_message"}

    # Check for consecutive same-role messages
    prev_role = None
    for idx, msg in enumerate(messages):
        if msg["role"] not in ("user", "assistant"):
            return {"error": f"Invalid role '{msg['role']}' at position {idx}", "code": "invalid_role"}

        if msg["role"] == prev_role:
            return {
                "error": f"Consecutive {msg['role']} messages at positions {idx - 1} and {idx}",
                "code": "consecutive_messages"
            }

        prev_role = msg["role"]


def parse_response_line(line):
    """
    Parses response lines while maintaining original format compatibility
    Returns multiple chunks for large content blocks
    """
    try:
        if line == DONE_MARKER:
            return []

        if line.startswith(DATA_PREFIX):
            json_str = line[len(DATA_PREFIX):].decode('utf-8')
            response_data = json.loads(json_str)

            if not isinstance(response_data, dict):
                return []

            model = response_data.get("model", "")
            choices = response_data.get("choices", [])
            if not choices:
                return []

            choice = choices[0]
            delta = choice.get("delta", {})

            # Correct content extraction for reasoner model
            content = delta.get("content")
            if not content and model == MODEL_REASONER:
                reasoning = delta.get("reasoning", {})
                content = reasoning.get("output", "")

            done = choice.get("finish_reason") == "stop"

            responses = []
            message_content = {
                "role": "assistant",
                "content": content,
                "images": None
            }

            # Handle reasoning steps for reasoner model
            if model == MODEL_REASONER:
                reasoning = delta.get("reasoning", {})
                reasoning_content = reasoning.get("output", "")
                if reasoning_content:
                    message_content["reasoning_steps"] = [
                        {"step": 1, "content": reasoning_content}
                    ]

            responses.append({
                "model": model,
                "message": message_content,
                "done": done
            })

            return responses

        return []
    except Exception as e:
        logging.error(f"Error parsing line: {e}")
        return []


def generate_streaming_response(request_payload, headers):
    """
    Generator that maintains original format while chunking responses
    """
    logging.debug(f"Sending request payload: {json.dumps(request_payload, indent=2)}")

    with requests.post(API_URL, headers=headers, json=request_payload, stream=True) as response:
        for line in response.iter_lines():
            if line:
                logging.debug(f"Received raw line: {line}")
                for chunk in parse_response_line(line):
                    if chunk:
                        logging.debug(f"Yielding chunk: {chunk}")
                        yield json.dumps(chunk) + "\n"


def handle_streaming_response(request_payload, headers):
    """
    Handles the creation of a streaming response using the provided request payload
    and headers. This function prepares a StreamingResponse object with a generator
    that produces the streaming content.

    Args:
        request_payload (dict): The payload of the request containing the necessary
        data for generating the streaming response.
        headers (dict): The headers to be included in the streaming response.

    Returns:
        StreamingResponse: An HTTP streaming response object with a specified
        JSON media type.
    """
    return StreamingResponse(generate_streaming_response(request_payload, headers), media_type=JSON_MEDIA_TYPE)


def handle_non_streaming_response(request_payload, headers):
    """
    Handles non-streaming response for a given request payload by making an API POST
    request. The function processes the API response and returns a structured JSON
    response containing model and message information. If an error occurs during
    request execution, it captures and returns the error details in a JSON response.

    Args:
        request_payload (dict): The payload to be sent to the API in JSON format.
        headers (dict): The HTTP headers to include in the API request.

    Raises:
        requests.exceptions.HTTPError: If the response from the API indicates an
        unsuccessful HTTP status code.
        Exception: For any unexpected errors that occur during the request
        execution or response processing.

    Returns:
        JSONResponse: A response containing either the retrieved model and message
        from the API, or error details if an exception is encountered.
    """
    try:
        response = requests.post(API_URL, headers=headers, json=request_payload)
        response.raise_for_status()
        response_data = response.json()
        message = response_data["choices"][0]["message"]
        model = response_data["model"]
        return JSONResponse(content={"model": model, "message": message, "done": True})
    except requests.exceptions.HTTPError as http_err:
        status_code = 400 if http_err.response.status_code < 500 else 500
        return JSONResponse(
            content={"error": f"HTTP error occurred: {http_err}"},
            status_code=status_code
        )
    except Exception as err:
        return JSONResponse(
            content={"error": f"An error occurred: {err}"},
            status_code=500
        )


@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    model = data.get("model")
    messages = data.get("messages")
    stream = data.get("stream", False)

    # Basic validation
    if not model or not messages:
        return JSONResponse(
            content={"error": "model and messages are required"},
            status_code=400
        )

    # Message sequence validation
    if validation_error := validate_message_sequence(messages, model):
        logging.error(f"Message sequence validation error: {validation_error}")
        return JSONResponse(
            content={
                "error": f"Invalid message sequence: {validation_error['error']}",
                "code": validation_error["code"]
            },
            status_code=400
        )

    # Rest of original implementation remains unchanged
    request_payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "frequency_penalty": 0.5,
        "max_tokens": 2048,
        "presence_penalty": 0.5,
        "temperature": 0.7,
        "top_p": 0.9,
        "response_format": {
            "type": "text"
        },
        "stop": None,
        "stream_options": None,
        "tools": None,
        "tool_choice": "none",
        "logprobs": False,
        "top_logprobs": None,
    }
    logging.debug(json.dumps(request_payload, indent=2))
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": JSON_MEDIA_TYPE}

    return (
        handle_streaming_response(request_payload, headers)
        if stream
        else handle_non_streaming_response(request_payload, headers)
    )


def create_model_dict(name):
    """Creates a dictionary representing the metadata of a model."""
    return {
        "name": name,
        "model": name,
        **MODEL_METADATA,
    }


@app.get("/api/tags")
async def get_tags():
    """
    Retrieves a list of available models with their respective metadata.
    This function handles an HTTP GET request to fetch a predefined list of models offered by the service.
    The response includes metadata for each model such as its name, size, digest, last modification date,
    and additional details like format and model family.
    Return:
        dict: A dictionary with key 'models' containing a list of dictionaries, each representing
        the metadata details of a model.
    """
    return {
        "models": [
            create_model_dict(MODEL_CHAT),
            create_model_dict(MODEL_REASONER),
        ]
    }


def run_server():
    """
    Starts and runs the server for the `fake_ollama_server` application using Uvicorn. This
    function initializes the server with specified configurations for host address, port,
    reload settings, and log level.

    Raises:
        Exception: If the server fails to start due to misconfiguration or environmental issues.
    """
    uvicorn.run(
        "fake_ollama_server:app",
        host=OLLAMA_ADDRESS,
        port=OLLAMA_PORT,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
