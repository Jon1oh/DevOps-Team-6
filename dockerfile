FROM python:3.14.8-slim
WORKDIR /app
COPY app.py io_manager.py logic_manager.py ai_manager.py data_manager.py fallback_ai.py requirements.txt .env .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python","app.py"]