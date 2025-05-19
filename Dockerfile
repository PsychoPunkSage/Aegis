FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11-utils \
    libx11-6 \
    xauth \
    tk-dev \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a script to run the application with Xvfb
RUN echo '#!/bin/bash\nXvfb :0 -screen 0 1024x768x16 &\nsleep 1\npython app.py' > /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 5900

CMD ["/app/start.sh"]