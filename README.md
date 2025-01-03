# How to Integrate DeepSeek into AI Assistant as a Third-Party Provider
This guide will walk you through the steps to integrate DeepSeek V3 into AI Assistant as a third-party provider into PyCharm 2024.3.1 (Professional Edition).
Data is routed through a fake OLLAMA server to DeepSeek.

## Prerequisites
- Ensure you have the necessary API key from DeepSeek
- Python knowledge

## Start Fake OLLAMA Server
### Docker
`docker run -e API_KEY=your_api_key_here -p 11434:11434 my-python-app`

### Python
1. **Setup repository**
  - Clone
  - Create virtual environment
  - Install [requirements.txt](requirements.txt)
2. **Create a Run Configuration for `fake_ollama_server.py`**
  - Open your project in PyCharm.
  - Navigate to `Run > Edit Configurations`.
  - Add a new configuration for [fake_ollama_server.py](fake_ollama_server.py).
3. **Add Your API Key to the Environment**
  - In the run configuration, go to the `Environment variables` section.
  - Add your DeepSeek API key as an environment variable.

## Configure PyCharm PRO AI Assistant
1. **Configure Third-Party AI Providers**
    - Go to `Tools > AI Assistant > Third-party AI providers`.
    - AI Assistant will automatically detect the server (approximately every minute).

2. **Select the Model**
    - Once the server is detected, you can choose the DeepSeek model from the available options.

3. **Use selected Model by entering a user prompt**

## Video and Screenshots
![](resources/HowTo.gif)

- **Third-Party AI Providers Configuration**  
  ![](resources/Tools-AI_Assistant_Third-party_AI_providers.png)

- **AI Assistant Chat Interface**  
  ![](resources/AI_Assistant_Chat.png)

## Notes
- Ensure the [fake_ollama_server.py](fake_ollama_server.py) is running before proceeding with the integration.
- If the server is not detected, restart the server and check the environment variables.

## Links
- [PyCharm AI Assistant](https://www.jetbrains.com/help/pycharm/ai-assistant.html)
- [DeepSeek Chat](https://chat.deepseek.com/)
- [DeepSeek API Docs](https://api-docs.deepseek.com/)
- [OLLAMA GitHub](https://github.com/ollama/ollama)

## Join the Community
We welcome contributions and feedback! If you have any suggestions or run into issues, please open an [issue](https://github.com/RobToMars/DeepSeek/issues) or submit a [pull request](https://github.com/RobToMars/DeepSeek/pulls).

Let’s make this integration even better together!

### Credits
- DeepSeek V3
  - With system prompts of AI Assistant of PyCharm 2024.3.1 (Professional Edition) and the web chat edition
- [RobToMars](https://github.com/RobToMars)
- [starkirby125918](https://github.com/starkirby125918)

---

For any issues or further assistance, please refer to the official DeepSeek documentation or contact the support team.
