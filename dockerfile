# --------------------------------------------
# 1. Base Image (Python 3.10 – stable for Pillow)
# --------------------------------------------
FROM python:3.10-slim

# --------------------------------------------
# 2. System Dependencies
# --------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------
# 3. Create app directory
# --------------------------------------------
WORKDIR /app

# --------------------------------------------
# 4. Copy project files
# --------------------------------------------
COPY . .

# --------------------------------------------
# 5. Install Python dependencies
# --------------------------------------------
RUN pip install --upgrade pip setuptools wheel

# Install numpy first
RUN pip install numpy==1.26.4

# Install heavy packages
RUN pip install torch==2.1.0 torchvision==0.16.0
RUN pip install segmentation_models_pytorch==0.3.3


RUN pip install -r requirements.txt

# --------------------------------------------
# 6. Expose port
# --------------------------------------------
EXPOSE 10000

# --------------------------------------------
# 7. Start Gunicorn server
# --------------------------------------------
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
