# How to Integrate DeepSeek into AI Assistant as a Third-Party Provider

This guide will walk you through the steps to integrate DeepSeek V3 into AI Assistant as a third-party provider into PyCharm 2024.3.1 (Professional Edition).

## Prerequisites
- Ensure you have the necessary API key from DeepSeek
- Python knowledge

## Steps to Integrate
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

4. **Configure Third-Party AI Providers**
    - Go to `Tools > AI Assistant > Third-party AI providers`.
    - AI Assistant will automatically detect the server (approximately every minute).

5. **Select the Model**
    - Once the server is detected, you can choose the DeepSeek model from the available options.

5. **Use selected Model by entering a user prompt**

![](resources/HowTo.gif)

## Screenshots

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

## Credits
- DeepSeek V3
  - With system prompts of AI Assistant of PyCharm 2024.3.1 (Professional Edition) and the web chat edition
- RobToMars

---

For any issues or further assistance, please refer to the official DeepSeek documentation or contact the support team.
