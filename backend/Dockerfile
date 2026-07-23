FROM python:3.10-slim

# 1. Install necessary system dependencies
# This is the stable version with all necessary libraries (libgl1, libtbbmalloc2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libopenblas-dev \
    libgtk2.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libtbb-dev \
    libtbbmalloc2 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    pkg-config \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup User and Working Directory
RUN useradd --create-home appuser
WORKDIR /app
ENV DEEPFACE_HOME /app

# 3. Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install llama-cpp-python compiled with OpenBLAS support for fast GGUF inference on CPU
ENV CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
RUN pip install --no-cache-dir llama-cpp-python

# 4. Explicitly Copy and Test Models (Ensure paths are correct)
# Explicitly copy models to the working directory.
COPY main.py .
COPY model_q.joblib .
COPY model_b.joblib .
COPY model_meta.joblib .
COPY scaler_q.joblib .
COPY scaler_b.joblib .

# This test should now run successfully if the files are named correctly.
RUN python -c "import joblib; joblib.load('model_q.joblib'); joblib.load('model_b.joblib'); joblib.load('model_meta.joblib'); joblib.load('scaler_q.joblib'); joblib.load('scaler_b.joblib'); print('Model integrity check passed!')"

# 5. Copy remaining files, transfer ownership, and switch user
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser

# 6. Define the command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]