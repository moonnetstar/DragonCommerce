FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 持久數據目錄（HuggingFace Spaces 的 /data 會持久保存）
RUN mkdir -p /data/stores
ENV PORT=8082
ENV DATA_DIR=/data

EXPOSE 8082

CMD ["python", "core/server.py"]
