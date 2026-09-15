FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd --system --user-group app
USER app

EXPOSE 8088

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8088"]
