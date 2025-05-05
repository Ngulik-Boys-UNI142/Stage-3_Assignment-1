# Start with a Python base image
FROM python:3.12-slim

# Install necessary system dependencies (including OpenCV's requirements)
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 && \
    rm -rf /var/lib/apt/lists/*

# Set a working directory inside the container
WORKDIR /app

# Copy only the requirements file first
COPY requirements.txt .

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install -r requirements.txt

# Copy your application code into the container
COPY . /app

# Set the virtual environment as the default Python environment
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port your app will run on
EXPOSE 5000

# Command to run your app
CMD ["python", "main.py"]
