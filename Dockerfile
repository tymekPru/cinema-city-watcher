FROM python:3.12-slim

# zoneinfo needs the tz database to resolve Europe/Prague; the slim image has none.
RUN pip install --no-cache-dir tzdata

WORKDIR /app
COPY src ./src
COPY front ./front

# Settings and data are mounted at runtime (see compose.yaml), nothing is baked in.
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py", "--keep-alive"]
