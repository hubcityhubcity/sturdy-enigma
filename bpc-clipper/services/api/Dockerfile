FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORAGE_ROOT=/data/storage \
    WHISPER_DOWNLOAD_ROOT=/data/models

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-whisper.txt ./
RUN pip install --upgrade pip && pip install -r requirements-whisper.txt

COPY . ./

RUN useradd --create-home --uid 10001 titan \
    && mkdir --parents /data/storage /data/models \
    && chown --recursive titan:titan /app /data

USER titan

EXPOSE 8000

CMD ["uvicorn", "production_entrypoint:app", "--host", "0.0.0.0", "--port", "8000"]
