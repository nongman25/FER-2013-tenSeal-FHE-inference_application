# ===== Build Stage =====
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies (will be discarded in final image)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ===== Runtime Stage =====
FROM python:3.10-slim

WORKDIR /app

# Install ONLY runtime dependencies (no build tools)
# libgl1 and libglib2.0-0 are needed for OpenCV at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directory for keys
RUN mkdir -p streamlit_app/keys

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app/app.py", "--server.address=0.0.0.0"]
