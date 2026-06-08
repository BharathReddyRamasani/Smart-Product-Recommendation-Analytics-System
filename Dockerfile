# Stage 1: Build the React Frontend
FROM node:18 AS frontend-builder

WORKDIR /app/frontend
# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy frontend source and build
COPY frontend/ .
# Since it's served by the backend, API requests will use relative paths
RUN npm run build


# Stage 2: Build the Python Backend & Serve
FROM python:3.11-slim

# Install system dependencies for ONNX and other compiled python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ /app/

# Copy the built React frontend from Stage 1 into the backend's static directory
COPY --from=frontend-builder /app/frontend/dist /app/static

# Create non-root user for Hugging Face Spaces security
RUN useradd -m -u 1000 user && \
    chown -R user:user /app
# Hugging Face spaces use 'user' as the default username, with home /home/user

# Switch to the non-root user
USER user

# Ensure huggingface/chroma cache directories are writeable
ENV XDG_CACHE_HOME=/home/user/.cache
RUN mkdir -p /home/user/.cache/chroma && chmod -R 777 /home/user/.cache

# Hugging Face exposes port 7860 by default
EXPOSE 7860

# Start FastAPI server on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
