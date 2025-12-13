# ===== Build Stage =====
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install CPU-only torch (minimal version, no torchvision needed)
# Use --extra-index-url to allow PyPI dependencies like jinja2
RUN pip install --no-cache-dir \
    torch==2.0.1+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install other requirements
RUN pip install --no-cache-dir -r requirements.txt

# ===== Runtime Stage =====
FROM python:3.10-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directory for HE contexts if it doesn't exist
RUN mkdir -p app/he_contexts

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
