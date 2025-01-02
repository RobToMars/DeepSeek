# -*- coding: UTF-8 -*-

""" Fake Ollama Server for testing Ollama integration with Deepseek for PyCharm IDE """

# Built-in Python libraries
import os
import json
import logging

# External Python libraries
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import requests
import uvicorn

# Package Python libraries

logging.basicConfig(level=logging.INFO)
app = FastAPI()

OLLAMA_ADDRESS = os.getenv("OLLAMA_ADDRESS", "0.0.0.0")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))

API_URL = os.getenv("API_URL", "https://api.deepseek.com/v1/chat/completions")
API_KEY = os.getenv("API_KEY", "YOUR_API_TOKEN")  # Retrieve the API key from the environment variable

MODEL_CHAT = "deepseek-chat"
MODEL_CODER = "deepseek-coder"
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


def parse_response_line(line):
    """
    Parses a single line of response from a specified format, extracting
    details about a model's output, including message content, completion
    status, and evaluation metrics if available.

    Args:
        line (str): The line of response to parse, expected to follow a
            predefined format.

    Returns:
        dict or None: A dictionary containing parsed response data, including
            the model name, assistant message content, completion status,
            and optional evaluation metrics (token counts), or None if the
            line does not conform to the expected format or contains errors.

    Raises:
        None explicitly. Logs errors if JSON decoding or data extraction
        fails during processing.
    """
    try:
        if line == DONE_MARKER:
            return None
        if line.startswith(DATA_PREFIX):
            response_data = json.loads(line[len(DATA_PREFIX) :])
            if not isinstance(response_data, dict) or "choices" not in response_data:
                return None
            choices = response_data["choices"]
            if len(choices) == 0:
                return None
            choice = choices[0]
            model = response_data["model"]
            content = choice["delta"]["content"]
            done = choice["finish_reason"] == "stop"
            output = {
                "model": model,
                "message": {"role": "assistant", "content": content, "images": None},
                "done": done,
            }
            if done:
                usage = response_data.get("usage", {})
                eval_count = usage.get("total_tokens", 0)
                prompt_eval_count = usage.get("prompt_tokens", 0)
                output.update({"eval_count": eval_count, "prompt_eval_count": prompt_eval_count})
            return output
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Failed to decode JSON or extract data: {e}, line: {line}")
        return None


def generate_streaming_response(request_payload, headers):
    """
    Generate a streaming response from a POST request to a specified API endpoint.

    This function sends a POST request to the provided API URL using the specified
    headers and request payload. It streams the response line by line, parses each
    line received, and yields the parsed response in JSON format. The function
    is designed for scenarios where data is continuously streamed from the server
    and needs to be processed incrementally.

    Args:
        request_payload (dict): The JSON payload to be sent in the POST request.
        headers (dict): The headers to be included in the POST request.

    Yields:
        str: A JSON-formatted string containing the parsed response object for
             each received line.
    """
    with requests.post(API_URL, headers=headers, json=request_payload, stream=True) as response:
        for line in response.iter_lines():
            parsed_response = parse_response_line(line)
            if parsed_response:
                yield json.dumps(parsed_response) + "\n"


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
        return JSONResponse(content={"error": f"HTTP error occurred: {http_err}"}, status_code=500)
    except Exception as err:
        return JSONResponse(content={"error": f"An error occurred: {err}"}, status_code=500)


@app.post("/api/chat")
async def chat(request: Request):
    """
    Handles the chat endpoint of the API. This function processes the incoming request payload, validates required
    fields, and routes the request to the appropriate response handler depending on the `stream` parameter.
    It communicates with an external service using the provided model and messages.

    Args:
        request (Request): The incoming HTTP POST request.

    Raises:
        ValueError: If the required 'messages' field is not provided in the request payload.

    Returns:
        JSONResponse: A JSON response containing either the result from the external service or an error message.
    """
    data = await request.json()
    model = data.get("model")
    messages = data.get("messages")
    stream = data.get("stream", False)
    if not messages:
        return JSONResponse(content={"error": "model and prompt are required"}, status_code=400)
    request_payload = {"model": model, "messages": messages, "stream": stream}
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
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
            create_model_dict(MODEL_CODER),
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
    uvicorn.run("fake_ollama_server:app", host=OLLAMA_ADDRESS, port=OLLAMA_PORT, reload=True, log_level="info")


if __name__ == "__main__":
    run_server()
