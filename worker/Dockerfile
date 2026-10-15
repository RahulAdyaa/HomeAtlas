FROM python:3.12-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg tesseract-ocr tesseract-ocr-hin libglib2.0-0 libgl1 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY worker/requirements.lock.txt /app/worker/requirements.lock.txt
RUN pip install --no-cache-dir -r worker/requirements.lock.txt
COPY worker /app/worker
COPY config /app/config
EXPOSE 8001
CMD ["python","-m","uvicorn","worker.app:app","--host","0.0.0.0","--port","8001"]
