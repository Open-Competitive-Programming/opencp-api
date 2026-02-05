FROM python:3.12

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/usr/src/app/src

CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
