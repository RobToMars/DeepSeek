# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 11434 available to the world outside this container
EXPOSE 11434

# Define environment variable
ENV OLLAMA_ADDRESS=0.0.0.0
ENV OLLAMA_PORT=11434

# Run fake_ollama_server.py when the container launches
CMD ["python", "fake_ollama_server.py"]
