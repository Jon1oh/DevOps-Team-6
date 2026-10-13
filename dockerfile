FROM python:3.14.8-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY data/ ./data
COPY models/ ./models
COPY managers/ ./managers
COPY app.py .env ./
CMD ["python","app.py"]