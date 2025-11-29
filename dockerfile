FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip setuptools wheel
RUN pip install numpy==1.26.4
RUN pip install torch==2.1.0 torchvision==0.16.0
RUN pip install segmentation_models_pytorch==0.3.3
RUN pip install -r requirements.txt

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
