FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project including data and faiss_index
COPY . /app/

# Create data directory if it doesn't exist
RUN mkdir -p /app/data /app/faiss_index

EXPOSE 8501

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8501"]