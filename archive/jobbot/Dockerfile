FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/

COPY job_bot/requirements.txt ./job_bot/
RUN pip install --no-cache-dir -r job_bot/requirements.txt

COPY api/requirements.txt ./api/
RUN pip install --no-cache-dir -r api/requirements.txt

COPY job_bot/ ./job_bot/
COPY api/ ./api/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
