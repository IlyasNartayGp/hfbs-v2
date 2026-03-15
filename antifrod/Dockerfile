FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/models

EXPOSE 9303
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9303", "--reload"]
