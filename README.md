# Oculex OCR

_Oculex_ (formerly *EOES*) is an OCR Stream Aggregator. It ingests video streams (e.g. RTSP), extracts text via OCR, and provides unified output. Designed to integrate nicely with Home Assistant for automations, monitoring, and logging.

---
<img width="2557" height="1302" alt="grafik" src="https://github.com/user-attachments/assets/430da324-8997-4fca-b197-768b15a1c05f" />
<img width="2551" height="1297" alt="grafik" src="https://github.com/user-attachments/assets/f6861372-d4fd-42d0-954b-615e3d3651b8" />
<img width="2558" height="1299" alt="grafik" src="https://github.com/user-attachments/assets/5f8d8958-c705-4bda-9bdb-4f531d99c6df" />

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Architecture & Tech Stack](#architecture--tech-stack)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Usage](#usage)  
- [Integration with Home Assistant](#integration-with-home-assistant)  
- [Limitations & Considerations](#limitations--considerations)  
- [Roadmap](#roadmap)  
- [Contributing](#contributing)  
- [License](#license)

---

## Overview

Oculex acts as a centralized node for OCR processing:

- Collects live video streams (e.g. RTSP from IP cameras).  
- Extracts text from these streams using OCR.  
- Normalizes and standardizes the output so downstream systems (like Home Assistant) can consume it easily.  
- Enables automations or alerts based on recognized text.  

---

## Features

- **Stream Ingestion** — Support for RTSP and potentially other stream protocols.  
- **Frame Sampling and OCR** — Periodic or event-triggered frame captures for OCR processing.  
- **Unified Output Format** — Text output normalized; includes metadata like timestamp, camera/source id, confidence, bounding boxes. 
- **Flexible OCR Engine Options** — Possibility to use different OCR engines (e.g. open source like Tesseract, EasyOCR, etc.).  
- **Home Assistant / Smart Home Integration** — Expose outputs as sensors, events, or via API/MQTT so Home Assistant workflows can use them.  
- **Containerization / Docker Support** — Easier deployment & portability with support as a home assistant add-on.

---

## Architecture & Tech Stack

| Component | Role |
|-----------|------|
| Stream listener / grabber | Connects to RTSP (or other) sources, pulls frames. |
| OCR Processor | Applies OCR on captured frames (configurable engine). |
| Output formatter | Normalizes results (timestamp, source, confidence, bounding box etc.). |
| API / Interface / Broker | Sends results to consumers (Home Assistant, MQTT, Webhooks etc.). |
| Configuration layer | Controls which streams, sampling rate, thresholds, OCR engine etc. |
| Deployment | Docker / container setup, optionally local or cloud deployment. |

Possible technologies:

- Programming Language: Python (or other)  
- OCR engines: Tesseract, EasyOCR, etc.
- API for output  
- RTSP support via ffmpeg / OpenCV  
- Docker for packaging  

---

## Installation

To be written.
