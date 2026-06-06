# Wol_xyz

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-host_network-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-167_passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-68%25-green)](tests/)

> 轻量级局域网设备远程管理工具 — WOL 开机 · SSH 关机 · 实时监控 · 定时任务 · 多渠道触发

![Dashboard](docs/images/screenshot.png)

---

## 功能概览

| 分类 | 功能 |
|------|------|
| **设备管理** | 卡片式多设备管理、设备类型自动识别、分组、批量操作 |
| **远程控制** | WOL 魔术包唤醒、SSH 关机（密码/密钥对）、自适应 Win/Linux/macOS 命令 |
| **状态监控** | ICMP Ping 双次确认 + WebSocket 实时推送、局域网扫描 |
| **定时任务** | 可视化频率配置（每天/每周/每月） |
| **触发源** | 巴法云（小爱语音）、HTTP API、MQTT、Telegram Bot |
| **通知渠道** | 邮件 SMTP、Webhook（飞书/企微）、Telegram |
| **其他** | 代理配置、时区控制、操作日志、用户管理 |

---

## 快速部署

### Docker（推荐）

```yaml
# docker-compose.yml
services:
  wol-xyz:
    image: xueayis/wol-xyz:latest
    container_name: wol-xyz
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    environment:
      - WEB_PORT=39090
      - TZ=Asia/Shanghai
```

```bash
docker compose up -d
```

访问 `http://<宿主机IP>:39090`，默认 `admin` / `admin`。

> ⚠️ 需要 `network_mode: host` 确保 WOL 广播和局域网扫描正常。macOS 不支持 Docker host 网络，请使用本地开发方式。

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `WEB_PORT` | `39090` | Web 端口 |
| `PING_INTERVAL` | `60` | Ping 间隔（秒） |
| `SCAN_SUBNET` | 自动 | 扫描子网 CIDR |
| `TZ` | `Asia/Shanghai` | 时区 |

---

## 本地开发

### 使用 run.sh（推荐）

```bash
./run.sh build     # 构建前端 + 启动后端（首次使用）
./run.sh start     # 仅启动后端（已构建过前端）
./run.sh stop      # 停止后端
./run.sh restart   # 重启后端
./run.sh rebuild   # 重新构建前端 + 重启后端
./run.sh status    # 查看运行状态
```

> 脚本自动管理虚拟环境、依赖安装、前端构建和后端进程，访问 `http://localhost:39090`。

### 手动启动

```bash
# 后端
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 39090

# 前端（另开终端）
cd frontend && npm install && npm run dev
```

前端开发 `http://localhost:5173`，API 代理到 `:39090`。

---

## 自动化测试

```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt

# 运行全部测试（167 个用例，覆盖率 68%）
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --rootdir=. --cov --cov-report=term-missing

# 按场景选择
pytest tests/ -m web_api          # Web API
pytest tests/ -m external_api     # External HTTP
pytest tests/ -m mqtt             # MQTT
pytest tests/ -m bemfa            # 巴法云
pytest tests/ -m telegram         # Telegram
pytest tests/ -m scheduler        # 定时任务
pytest tests/ -m cross_platform   # 跨平台
pytest tests/ -m multi_device     # 多设备/分组

# 覆盖率
pytest tests/ --cov=backend/app --cov-report=html
```

CI 流水线：push/PR 自动测试 → tag 推送时自动构建 Docker 镜像并发布 Release。

---

## 外部触发

### HTTP API

```bash
curl "http://<IP>:39090/api/external/trigger?token=TOKEN&mac=AA:BB:CC:DD:EE:FF&action=wake"
```

<details>
<summary>Home Assistant 集成</summary>

```yaml
rest_command:
  wol_xyz_wake:
    url: "http://<IP>:39090/api/external/trigger"
    method: GET
    params:
      token: "YOUR_TOKEN"
      mac: "AA:BB:CC:DD:EE:FF"
      action: "wake"
```

</details>

### 巴法云

配置 UID + Topic，通过米家/小爱语音控制开关机。

### MQTT

配置 Broker + Topic，发送 `on`/`off`/`wake`/`shutdown` 或 JSON `{"action":"wake"}`。

### Telegram Bot

通过 [@BotFather](https://t.me/BotFather) 创建 Bot → 添加触发源 → 支持 `/devices`、`/groups`、`/scan`、`/logs` 命令。

---

## 设备配置要求

| 功能 | Windows | Linux | macOS |
|------|---------|-------|-------|
| **WOL** | BIOS 启用 + 网卡驱动开启 + 关闭快速启动 | BIOS 启用 + `ethtool -s eth0 wol g` | 节能 → 唤醒以供网络访问（仅有线） |
| **SSH 关机** | 启用 OpenSSH Server | 默认已有 sshd | 默认已有 sshd |

---

## API 文档

| 地址 | 说明 |
|------|------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI Schema |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI · SQLAlchemy 2 (async) · APScheduler · paho-mqtt |
| 前端 | Vue 3 · TypeScript · Naive UI · Pinia · Vite 6 |
| 数据库 | SQLite (aiosqlite) |
| 测试 | pytest · pytest-asyncio · httpx · 虚拟设备状态机 |
| CI/CD | GitHub Actions（test → build → release） |
| 部署 | Docker multi-stage · host network · amd64/arm64 |

---

## License

MIT
