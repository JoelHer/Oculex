FROM python

# Set the working directory
WORKDIR /app

# Update the package list and install Tesseract along with other dependencies
RUN apt-get update && \
    apt-get install -y \
        tesseract-ocr \
        libtesseract-dev \
        ffmpeg \
        libsm6 \
        libxext6 \
        && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]
