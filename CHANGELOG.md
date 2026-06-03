# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-06-04

### Added

- Web 管理面板（Vue 3 + Naive UI，iOS 风格 UI）
- 多设备管理与分组（卡片式界面）
- 实时设备状态监控（ICMP Ping + WebSocket 推送，按需轮询）
- Wake-on-LAN 远程开机
- SSH 远程关机（支持 Windows / Linux / macOS）
- 定时任务（Cron 表达式）
- 外部触发源：巴法云、HTTP API、MQTT、Telegram Bot
- 通知渠道：邮件（SMTP）、Webhook（内置飞书/企业微信模板）
- 操作日志记录
- Docker 部署（multi-stage build，host 网络模式）
- 局域网扫描（UDP 广播 + ARP 表）
- WoL 配置指引（Windows / Linux / macOS）
