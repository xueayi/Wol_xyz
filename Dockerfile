FROM node:20-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping openssh-client sshpass net-tools dnsutils && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY VERSION ./
COPY --from=frontend-build /build/dist ./frontend/dist/

RUN mkdir -p /app/data

ENV DATABASE_URL="sqlite+aiosqlite:///./data/wol_xyz.db"
ENV WEB_PORT=39090
ENV TZ="Asia/Shanghai"

EXPOSE 39090

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "39090"]
