FROM python:3.10-slim

# Install basic packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (current LTS version) and npm
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs


# Set working dir
WORKDIR /usr/src/app

# Install Python deps...
COPY requirements.txt /requirements.txt
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /requirements.txt

COPY . /usr/src/app/

WORKDIR /usr/src/app/frontend-vue
COPY frontend-vue/package*.json ./
RUN npm install
COPY frontend-vue .
RUN npm run build

WORKDIR /usr/src/app

EXPOSE 5000
ENV EASYOCR_MODULE_PATH=/data/easyocr-models

CMD ["python", "server.py"]
