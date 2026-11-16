FROM python:3.14.8-slim
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# copy the entire project automatically. Saves time from updating the Dockerfile every time a new folder is created.
COPY . .
EXPOSE 8000
CMD ["python","run.py"]