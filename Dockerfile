# Moa365 MCP Proxy — PlayMCP in KC (linux/amd64)
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .

# KC 가 PORT 환경변수를 주면 그 포트로, 아니면 8080 으로 리슨.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
