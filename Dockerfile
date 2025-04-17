# Use the official Python slim image
FROM python:3.10-slim

# Install dependencies for OpenCV, easyocr, and other required libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements file and install dependencies
COPY requirements.txt /requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /requirements.txt

# Copy all application files to the root directory (after installing dependencies)
COPY . /usr/src/app/

# Expose port 5000
EXPOSE 5000

# Set environment variables if needed
ENV EASYOCR_MODULE_PATH=/data/easyocr-models

# Run the application
CMD ["python", "main.py"]
