# Changelog

All notable changes to this project will be documented in this file.

## [1.0.3] - 2026-06-06

### Added

- 远程关机内联引导：开启关机后显示配置步骤提示卡片和详细说明链接
- 密钥对公钥区域增加部署命令提示（Linux/macOS/Windows）
- 生成密钥对按钮旁增加「需将公钥部署到目标设备」提示

### Fixed

- SSH 用户名表单项排版两行：label-width 增至 90px 并强制 label 不换行
- 私钥缺少 PEM 头尾标记时自动补全，防止 `error in libcrypto` 报错
- 编辑设备时 payload 清除 DeviceOut 只读字段，避免请求携带无效属性

## [1.0.2] - 2026-06-06

### Added

- SSH 密钥对一键生成：设备编辑中新增「生成密钥对」按钮（Ed25519），私钥自动填入、公钥一键复制
- 凭据状态提示：已配置密码/密钥时编辑弹窗显示「已配置，留空保持不变」，避免误清空
- 使用指引增加「远程关机」完整配置说明：SSH 开启方法、用户名查看、密钥对部署步骤、Linux 免密 sudo
- 设备编辑中远程关机旁增加「配置说明」快捷入口，跳转到使用指引

### Fixed

- SSH 密钥对关机失败（`error in libcrypto`）：写入临时文件前 `strip()` + 补末尾换行
- 设备编辑弹窗中 SSH 用户名表单项排版变成两行的布局问题

## [1.0.1] - 2026-06-06

### Fixed

- Docker 容器内扫描极慢且不稳定：Linux 下改用 `/proc/net/arp` 直读内核 ARP 表（0.7ms vs `arp -a` 反查 DNS 超时），过滤 incomplete 条目
- 容器缺少 `ip` 命令导致 IP 检测、Docker 子网过滤、ARP 广播、网关检测全部静默失败：所有网络工具调用增加 `ifconfig`/`route -n` 降级方案
- Docker 环境下扫描设备数从 1~11 不稳定提升到 14 台稳定，耗时从 12~36s 降至 ~7s

## [1.0.0] - 2026-06-06

### Changed

- 局域网扫描重构：多轮 UDP 探测 + 子网广播 + Linux 原生 ARP 广播，大幅提升设备发现率和稳定性
- 自适应 ARP 等待：轮询 ARP 表直至设备数稳定，替代固定 3 秒等待
- hostname 解析加速：多方法并发竞赛取首个结果，替代串行尝试（单设备从最长 18s 降至 3s 内）
- 本机 IP 检测优先从物理网卡获取，避免 VPN/代理干扰导致扫描失败
- 使用指引中 API 触发源的 Home Assistant 示例改为折叠展示
- 触发源连接失败改为指数退避重试（5s → 300s），首次失败降为 WARNING，抑制重复日志刷屏
- httpx 日志级别设为 WARNING，减少无效 INFO 输出

### Added

- 扫描防抖锁：同一时间仅允许一次扫描，重复请求返回 409
- 新增扫描配置环境变量：SCAN_SUBNET / SCAN_TIMEOUT / SCAN_ROUNDS / SCAN_HOSTNAME_CONCURRENCY / SCAN_HOSTNAME_TIMEOUT
- ARP 子网过滤兜底：检测子网与实际 LAN 不匹配时自动回退到全量 ARP 结果

### Removed

- 移除 mac-vendor-lookup 依赖及厂商识别功能（大量随机 MAC 导致识别无效且产生异常日志）
- 移除 oui_detect.py 模块，设备类型改为纯 hostname 关键词匹配

## [0.4.0] - 2026-06-05

### Added

- SSH 密钥对认证：远程关机支持密码或 PEM 私钥两种认证方式
- 删除 Telegram 通知渠道时自动关闭对应触发源的「同步通知渠道」开关
- 多平台关机命令：自动根据设备类型（Windows/Linux/macOS）选择正确的关机指令
- JWT 密钥自动生成：首次启动时自动生成安全的 JWT Secret，无需手动配置

### Changed

- 远程关机与设备类型绑定：仅 Windows/Linux/macOS 设备可启用远程关机，去除独立的"目标系统"选择
- 通知渠道侧栏入口从「+ 新建」改为「管理」
- SSH 密码传递改用 `sshpass -e` 环境变量方式，避免密码出现在进程参数列表中
- API Token 比较改用 `hmac.compare_digest` 常量时间比较，防止时序攻击

### Fixed

- MQTT 触发源 broker/host 字段名不一致导致连接失败
- Telegram Bot 日志状态字段名错误（`log.status` → `log.result`）
- 定时关机任务未检查 `shutdown_enabled` 导致对未启用关机的设备发送 SSH 命令
- 巴法云/MQTT 通知中 `device_name` 变量作用域错误
- SPA catch-all 路由拦截 `/docs`、`/redoc` 等 FastAPI 内置路径
- 定时任务弹窗中无效的 `watch(emit)` 监听

### Removed

- 删除遗留的 `main.py`、`config.ini`、`install.sh`（旧版单文件架构残留）
- 移除独立的 `os_type` 字段，关机命令直接从 `device_type` 推导

## [0.3.3] - 2026-06-05

### Added

- Home Assistant 集成示例：README 和应用内使用指引新增 `rest_command` 配置及自动化 YAML 示例

### Fixed

- 巴法云触发源握手验证：发送订阅报文后等待服务端 ACK（`cmd=0`）再标记为在线，UID 无效时不再错误显示「在线」状态

### Changed

- 应用图标更新为渐变色 SVG 图标

## [0.3.2] - 2026-06-05

### Added

- 触发源状态监控：侧边栏新增「触发源状态」卡片，实时显示各触发渠道连接状态（在线/连接中/离线/禁用）
- 代理配置：设置面板新增代理设置（HTTP/SOCKS5），Telegram Bot 和 Webhook 通知自动应用代理，保存后立即生效无需重启
- 时区环境变量 `TZ`：统一控制所有时间显示，默认 `Asia/Shanghai`，支持通过环境变量或 `.env` 覆盖
- 局域网扫描增强：新增 NetBIOS、mDNS、gethostbyaddr 多种主机名解析方式
- Linux 部署时自动识别并过滤 Docker 创建的虚拟网卡和子网
- 新增 `GET /api/settings/timezone` 接口供前端获取当前时区配置

### Changed

- 代理设置表单始终可编辑和测试，启用开关仅控制是否在实际请求中应用代理
- 所有后端时间戳统一使用 `tz_now()` 生成（替代 `datetime.utcnow()`），确保时间一致性
- 所有 API 响应的时间字段附带时区偏移信息（如 `+08:00`），前端无需额外转换
- 定时任务编辑/删除按钮优化间距
- 触发源管理表格操作列边框对齐修复
- 巴法云配置说明措辞修正（插座→开关，Topic→主题）
- 触发源管理和定时任务弹窗重新打开时自动回到一级页面
- 分组管理/批量管理按钮适配手机竖屏布局
- Dockerfile 和 docker-compose.yml 新增 `TZ` 环境变量

### Fixed

- 最近触发记录时间偏差 8 小时的 UTC 时区问题
- 前端 `RecentLogs` 时间解析兼容带时区后缀的 ISO 字符串

## [0.3.1] - 2026-06-05

### Fixed

- 修复设备概览列表视图按钮点击无效的问题（viewMode 未传递给子组件）
- 实现完整的列表视图模式（紧凑横向布局，显示状态点、设备名、IP、MAC、最后在线时间及操作按钮）

## [0.3.0] - 2026-06-04

### Added

- 设备类型自动识别（OUI 指纹 + 路由器 DNS 反向解析）
- 局域网扫描自动获取设备名称（通过网关 DNS 反向查询）
- 设备类型选择器（windows/macos/linux/ipad/iphone/android/nas/router 等）
- 设备卡片图标根据设备类型动态切换
- 批量管理功能（全选/批量删除/批量移动分组）
- 定时任务界面优化（可视化频率选择替代原始 cron 表达式输入）
- 扫描结果显示设备名称列和设备类型列
- 扫描结果过滤已添加设备，支持多选批量添加
- 添加设备时自动使用 hostname 作为默认名称
- 非 WoL 设备标记（iPhone/iPad/Android/手表/IoT）
- GitHub Actions CI/CD（Docker build + push to Docker Hub，tag 触发）

### Changed

- 在线状态检测更稳定（双次确认机制，防止误判离线）
- MAC 地址解析修复前导零丢失问题
- 「最后在线」时间修正为 UTC 正确解析
- 设备编辑按钮改为独立按钮，避免与批量选择框重叠

### Fixed

- 创建设备时 `device_type` 字段未正确传入数据库
- ARP 表解析在 macOS 下 MAC 地址缺少前导零（如 `e:e6` → `0E:E6`）
- OUI 检测因 MAC 地址未标准化导致匹配失败

## [0.2.0] - 2026-06-04

### Changed

- 项目重命名为 Wol_xyz（原 XiaoXue WoL）
- 环境变量移除 `WOM_` 前缀（`WOM_WEB_PORT` → `WEB_PORT`）
- docker-compose 移除用户名/密码/密钥环境变量配置，改为 Web 面板管理
- 「使用指引」合并 WoL 配置内容，新增 API 手册 tab
- HTTP API 触发源统一显示为 API
- 数据库文件从 `xiaoxue_wol.db` 更名为 `wol_xyz.db`

### Added

- 通知渠道可选通知类型：「触发通知」（命令发送时）和「任务成功通知」（设备状态确认后）
- 用户管理功能（修改用户名、密码、重新生成 JWT 密钥）
- Telegram 通知渠道类型（独立添加或从触发源同步）
- 触发源 Telegram Bot「同步通知渠道」开关
- 使用指引增加 API 手册 tab（Swagger UI / ReDoc / OpenAPI JSON）
- README 增加虚拟环境本地开发说明

### Removed

- docker-compose 中的 `WOM_ADMIN_USERNAME`、`WOM_ADMIN_PASSWORD`、`WOM_SECRET_KEY` 环境变量
- 功能设置中的独立「WoL 配置」按钮（已合并到使用指引）

## [0.1.0] - 2026-06-04

### Added

- Web 管理面板（Vue 3 + Naive UI）
- 多设备管理与分组（卡片式界面）
- 实时设备状态监控（ICMP Ping + WebSocket 推送，按需轮询）
- Wake-on-LAN 远程开机
- SSH 远程关机（支持 Windows / Linux / macOS）
- 定时任务（Cron 表达式）
- 外部触发源：巴法云、API、MQTT、Telegram Bot
- 通知渠道：邮件（SMTP）、Webhook（内置飞书/企业微信模板）
- 操作日志记录
- Docker 部署（multi-stage build，host 网络模式）
- 局域网扫描（UDP 广播 + ARP 表）
- WoL 配置指引（Windows / Linux / macOS）
