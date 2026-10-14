FROM python:3.14.8-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY data/ ./data
COPY models/ ./models
COPY tests/ ./tests
COPY managers/ ./managers
COPY app.py pytest.ini .env ./
CMD ["python","app.py"]