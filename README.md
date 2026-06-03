# XiaoXue WoL - 局域网设备管理

一个轻量级的局域网设备远程管理工具，提供 Web 管理面板，支持 Wake-on-LAN 远程开机、SSH 远程关机、设备状态监控、定时任务和多渠道通知。

## 功能特性

- **多设备管理**：通过卡片式界面管理所有局域网设备
- **设备分组**：按办公设备、家庭设备等自定义分类
- **实时状态监控**：ICMP Ping 定期检测设备在线状态，WebSocket 实时推送
- **远程开机**：WOL 魔术包唤醒（需目标设备开启 WOL）
- **远程关机**：SSH 连接执行关机命令（支持密码认证）
- **定时任务**：Cron 表达式驱动的自动开关机
- **外部触发源**：
  - 巴法云（Bemfa）TCP 协议 — 支持米家/小爱/Home Assistant
  - HTTP API Token — 通用 REST 接口
  - MQTT — IoT 标准协议
- **通知渠道**：邮件（SMTP）和通用 Webhook（内置飞书/企业微信模板），支持多实例
- **操作日志**：记录所有操作的成功/失败详情

## 快速开始

### Docker 部署（推荐）

```bash
git clone https://github.com/xueayi/XiaoXue_WoL.git
cd XiaoXue_WoL
docker compose up -d
```

访问 `http://<宿主机IP>:39090`，默认账号 `admin` / `admin`。

> **重要**：使用 `network_mode: host` 确保 WOL 广播和局域网扫描正常工作。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WOM_WEB_PORT` | `39090` | Web 面板端口 |
| `WOM_ADMIN_USERNAME` | `admin` | 管理员用户名 |
| `WOM_ADMIN_PASSWORD` | `admin` | 管理员初始密码 |
| `WOM_SECRET_KEY` | 随机值 | JWT 签名密钥（生产环境请修改） |
| `WOM_PING_INTERVAL` | `60` | Ping 检测间隔（秒） |

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 39090

# 前端
cd frontend
npm install
npm run dev
```

## 目标设备配置

### 远程开机（WOL）

#### Windows

1. **BIOS**：启用 Wake on LAN / PCI-E 唤醒
2. **设备管理器**：网卡属性 → 电源管理 → 允许唤醒；高级 → 启用「魔术封包唤醒」
3. **关闭快速启动**：控制面板 → 电源选项

#### Linux

1. **BIOS**：启用 Wake on LAN
2. **安装 ethtool**：`sudo apt install ethtool`
3. **启用 WoL**：`sudo ethtool -s eth0 wol g`（`eth0` 替换为实际网卡名）
4. **持久化**：编辑 `/etc/network/interfaces` 或创建 systemd 服务使其开机生效

#### macOS

1. 系统设置 → 节能 → 勾选「唤醒以供网络访问」
2. 仅支持有线以太网连接，Wi-Fi 下 WoL 不可用

### 远程关机（SSH）

1. **Windows**：启用 OpenSSH Server（设置 → 应用 → 可选功能）
2. **Linux / macOS**：通常自带 SSH，确保 sshd 已启用
3. 确保 SSH 端口 22 未被防火墙阻止
4. 在 Web 面板中启用远程关机并填写 SSH 凭据

## 外部触发

### HTTP API

```bash
# GET 方式
curl "http://<IP>:39090/api/external/trigger?token=YOUR_TOKEN&mac=AA:BB:CC:DD:EE:FF&action=wake"

# POST 方式
curl -X POST "http://<IP>:39090/api/external/trigger?token=YOUR_TOKEN&device_id=1&action=shutdown"
```

### 巴法云

在触发源管理中配置巴法云 UID 和 Topic，即可通过米家/小爱语音控制设备开关机。

### MQTT

配置 MQTT Broker 地址和 Topic，发送 `on`/`off` 消息触发设备操作。

## 技术栈

- **后端**：FastAPI + SQLAlchemy + APScheduler + paho-mqtt
- **前端**：Vue 3 + Naive UI + Pinia + Vite
- **数据库**：SQLite
- **部署**：Docker (host 网络模式)

## License

MIT
