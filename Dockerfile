# Multi-stage Dockerfile for complete React + FastAPI app
FROM node:18-alpine AS frontend-builder

# Build React frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /frontend/build ./static

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Create non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Start server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
