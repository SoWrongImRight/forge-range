FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
