# test_fake_ollama_server.py
import unittest
import requests
import json
import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Constants
OLLAMA_ADDRESS = "127.0.0.1"
OLLAMA_PORT = 11434
API_URL = f"http://{OLLAMA_ADDRESS}:{OLLAMA_PORT}/api/chat"
MODEL_CHAT = "deepseek-chat"
MODEL_REASONER = "deepseek-reasoner"


class TestFakeOllamaServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the fake Ollama server before running tests."""
        logging.info("Starting fake Ollama server...")
        cls.server_process = subprocess.Popen(
            ["python", "fake_ollama_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait for server to be ready with retries
        max_retries = 5
        retry_delay = 2
        health_url = f"http://{OLLAMA_ADDRESS}:{OLLAMA_PORT}/health"
        
        for attempt in range(max_retries):
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    logging.info("Fake Ollama server started and healthy")
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                logging.info(f"Waiting for server to start... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
        
        cls.server_process.terminate()
        cls.server_process.wait()
        raise Exception("Failed to start fake Ollama server")

    @classmethod
    def tearDownClass(cls):
        """Stop the fake Ollama server after running tests."""
        logging.info("Stopping fake Ollama server...")
        try:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)
            logging.info("Fake Ollama server stopped.")
        except subprocess.TimeoutExpired:
            cls.server_process.kill()
            logging.warning("Had to forcefully kill server process")

    @classmethod
    def tearDownClass(cls):
        """Stop the fake Ollama server after running tests."""
        logging.info("Stopping fake Ollama server...")
        cls.server_process.terminate()
        cls.server_process.wait()
        logging.info("Fake Ollama server stopped.")

    def test_chat_model_basic(self):
        """Test basic chat functionality with deepseek-chat."""
        payload = {
            "model": MODEL_CHAT,
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "stream": False,
        }
        response = requests.post(API_URL, json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model"], MODEL_CHAT)
        self.assertTrue(data["done"])
        self.assertIn("content", data["message"])
        self.assertIsInstance(data["message"]["content"], str)

    def test_reasoner_model_basic(self):
        """Test basic reasoning functionality with deepseek-reasoner."""
        payload = {
            "model": MODEL_REASONER,
            "messages": [{"role": "user", "content": "What is 2 + 2?"}],
            "stream": False,
        }
        response = requests.post(API_URL, json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model"], MODEL_REASONER)
        self.assertTrue(data["done"])
        self.assertIn("content", data["message"])
        # self.assertIn("reasoning_steps", data["message"])
        # self.assertIsInstance(data["message"]["reasoning_steps"], list)

    def test_streaming_chat(self):
        """Test streaming response with chat model."""
        payload = {
            "model": MODEL_CHAT,
            "messages": [{"role": "user", "content": "Tell me a story"}],
            "stream": True,
        }
        response = requests.post(API_URL, json=payload, stream=True)
        
        self.assertEqual(response.status_code, 200)
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                self.assertIn("model", data)
                self.assertIn("message", data)
                self.assertIn("done", data)

    def test_streaming_reasoner(self):
        """Test streaming response with reasoner model."""
        payload = {
            "model": MODEL_REASONER,
            "messages": [{"role": "user", "content": "Explain quantum computing"}],
            "stream": True,
        }
        response = requests.post(API_URL, json=payload, stream=True)
        
        self.assertEqual(response.status_code, 200)
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                self.assertIn("model", data)
                self.assertIn("message", data)
                self.assertIn("done", data)
                if data["done"]:
                    self.assertIn("reasoning_metrics", data)

    def test_invalid_model(self):
        """Test error handling for invalid model."""
        payload = {
            "model": "invalid-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        }
        response = requests.post(API_URL, json=payload)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_missing_messages(self):
        """Test error handling for missing messages."""
        payload = {
            "model": MODEL_CHAT,
            "stream": False,
        }
        response = requests.post(API_URL, json=payload)
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_model_tags_endpoint(self):
        """Test the /api/tags endpoint."""
        response = requests.get(f"http://{OLLAMA_ADDRESS}:{OLLAMA_PORT}/api/tags")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        models = [m["name"] for m in data["models"]]
        self.assertIn(MODEL_CHAT, models)
        self.assertIn(MODEL_REASONER, models)


if __name__ == "__main__":
    unittest.main()
