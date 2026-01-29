# docker/Dockerfile
# Build a portable image for the Streamlit dashboard
FROM python:3.11-slim

WORKDIR /app

# OS deps for psycopg2, others
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Default env for Streamlit
ENV PORT=8501
ENV STREAMLIT_SERVER_ENABLE_CORS=false

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
