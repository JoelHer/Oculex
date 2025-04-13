# Use official Python slim image
FROM python

# Install dependencies for OpenCV and easyocr
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt /requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /requirements.txt

# Copy all application files to the root directory
COPY . /

# Expose port 5000
EXPOSE 5000

CMD ["python", "main.py"]
