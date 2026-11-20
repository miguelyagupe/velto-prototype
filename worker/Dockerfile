FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core nodejs ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e . -r requirements-capture.txt piper-tts==1.8.0 && python -m playwright install --with-deps chromium
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
