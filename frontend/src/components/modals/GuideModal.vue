<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show'])

const activeTab = ref('quickstart')
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="使用指引" style="width: 700px" :bordered="false">
    <div class="guide-content">
      <n-tabs v-model:value="activeTab" type="segment" animated>
        <n-tab-pane name="quickstart" tab="快速开始">
          <div class="section">
            <h3>基本使用</h3>
            <ol>
              <li><b>添加设备</b>：点击「手动添加」或「扫描局域网」发现设备</li>
              <li><b>分组管理</b>：在设备概览区管理设备分组归属</li>
              <li><b>远程开机</b>：点击设备卡片上的「开机」按钮发送 WOL 魔术包</li>
              <li><b>远程关机</b>：先在设备配置中启用并填写 SSH 信息</li>
              <li><b>定时任务</b>：设置 Cron 表达式自动执行开关机</li>
              <li><b>通知渠道</b>：配置邮件或 Webhook 接收操作通知</li>
            </ol>
          </div>
        </n-tab-pane>

        <n-tab-pane name="wol" tab="WoL 配置">
          <div class="section">
            <h3>远程开机 (Wake-on-LAN)</h3>
            <h4>Windows</h4>
            <ol>
              <li><b>BIOS</b>：电源管理 → 启用 Wake on LAN / PCI-E 唤醒</li>
              <li><b>设备管理器</b>：网卡 → 属性 → 电源管理 → 勾选「允许此设备唤醒计算机」</li>
              <li><b>网卡高级属性</b>：启用「魔术封包唤醒」(Wake on Magic Packet)</li>
              <li><b>关闭快速启动</b>：控制面板 → 电源选项 → 关闭快速启动</li>
            </ol>
            <h4>Linux</h4>
            <ol>
              <li><b>BIOS</b>：同上，启用 Wake on LAN</li>
              <li><b>安装 ethtool</b>：<code>sudo apt install ethtool</code></li>
              <li><b>启用 WoL</b>：<code>sudo ethtool -s eth0 wol g</code>（eth0 替换为实际网卡名）</li>
              <li><b>持久化</b>：编辑 <code>/etc/network/interfaces</code> 或创建 systemd 服务使其开机生效</li>
            </ol>
            <h4>macOS</h4>
            <ol>
              <li>系统设置 → 节能 → 勾选「唤醒以供网络访问」</li>
              <li>仅支持有线以太网连接，Wi-Fi 下 WoL 不可用</li>
            </ol>

            <n-divider />

            <h3>远程关机 (SSH)</h3>
            <ol>
              <li><b>Windows</b>：设置 → 应用 → 可选功能 → 添加 OpenSSH Server</li>
              <li><b>Linux / macOS</b>：通常自带 SSH，确保 sshd 已启用</li>
              <li>确保 SSH 端口 22 未被防火墙阻止</li>
              <li>在设备设置中启用远程关机并填写 SSH 凭据</li>
            </ol>
          </div>
        </n-tab-pane>

        <n-tab-pane name="triggers" tab="触发源">
          <div class="section">
            <n-collapse>
              <n-collapse-item title="API" name="api">
                <p class="trigger-desc">通过带 Token 的 HTTP 请求触发设备开关机，适用于脚本、自动化工具或第三方平台调用。</p>
                <h4>配置步骤</h4>
                <ol>
                  <li>在「触发源管理」中添加 API 类型的触发源</li>
                  <li>设置 Token 和绑定的目标设备</li>
                  <li>使用生成的接口地址进行调用</li>
                </ol>
                <h4>请求示例</h4>
                <div class="code-block">
                  <div class="code-label">GET 方式 — 远程开机</div>
                  <code>GET /api/external/trigger?token=YOUR_TOKEN&amp;mac=AA:BB:CC:DD:EE:FF&amp;action=wake</code>
                </div>
                <div class="code-block">
                  <div class="code-label">GET 方式 — 远程关机</div>
                  <code>GET /api/external/trigger?token=YOUR_TOKEN&amp;device_id=1&amp;action=shutdown</code>
                </div>
                <div class="code-block">
                  <div class="code-label">cURL 示例</div>
                  <code>curl "http://&lt;IP&gt;:39090/api/external/trigger?token=xxx&amp;mac=AA:BB:CC:DD:EE:FF&amp;action=wake"</code>
                </div>
                <p class="trigger-tip">参数说明：<code>token</code> 必填；设备可用 <code>mac</code> 或 <code>device_id</code> 指定；<code>action</code> 为 <code>wake</code> 或 <code>shutdown</code></p>
              </n-collapse-item>

              <n-collapse-item title="巴法云 (Bemfa)" name="bemfa">
                <p class="trigger-desc">通过巴法云（Bemfa）TCP 协议接入，支持米家、小爱同学、Home Assistant 等智能家居平台语音控制设备开关机。</p>
                <h4>配置步骤</h4>
                <ol>
                  <li>在 <a href="https://cloud.bemfa.com" target="_blank" style="color:#007AFF">cloud.bemfa.com</a> 注册并获取 UID（私钥）</li>
                  <li>在巴法云控制台创建一个 Topic（主题），类型选「插座」</li>
                  <li>在「触发源管理」中添加巴法云类型的触发源，填入 UID 和 Topic</li>
                  <li>绑定要控制的目标设备</li>
                  <li>在米家 / 小爱中添加巴法云设备，即可语音控制</li>
                </ol>
                <h4>控制指令</h4>
                <div class="code-block">
                  <div class="code-label">开机（米家/小爱）</div>
                  <code>"小爱同学，打开 [设备名称]"  →  发送 on  →  WOL 唤醒</code>
                </div>
                <div class="code-block">
                  <div class="code-label">关机（米家/小爱）</div>
                  <code>"小爱同学，关闭 [设备名称]"  →  发送 off  →  SSH 关机</code>
                </div>
                <p class="trigger-tip">提示：巴法云 Topic 类型需选「插座」才能在米家中识别为开关设备</p>
              </n-collapse-item>

              <n-collapse-item title="MQTT" name="mqtt">
                <p class="trigger-desc">通过 MQTT 协议接入，适用于 IoT 设备、Home Assistant、Node-RED 等场景。</p>
                <h4>配置步骤</h4>
                <ol>
                  <li>准备一个 MQTT Broker（如 EMQX、Mosquitto 或云服务）</li>
                  <li>在「触发源管理」中添加 MQTT 类型的触发源</li>
                  <li>填写 Broker 地址、端口、用户名密码（如有）和订阅 Topic</li>
                  <li>绑定要控制的目标设备</li>
                </ol>
                <h4>消息格式</h4>
                <div class="code-block">
                  <div class="code-label">开机</div>
                  <code>Topic: wol_xyz/device1 &nbsp; Payload: on</code>
                </div>
                <div class="code-block">
                  <div class="code-label">关机</div>
                  <code>Topic: wol_xyz/device1 &nbsp; Payload: off</code>
                </div>
                <div class="code-block">
                  <div class="code-label">mosquitto_pub 示例</div>
                  <code>mosquitto_pub -h &lt;BROKER_IP&gt; -t "wol_xyz/device1" -m "on"</code>
                </div>
                <p class="trigger-tip">Payload 仅需发送 <code>on</code>（开机）或 <code>off</code>（关机），不区分大小写</p>
              </n-collapse-item>

              <n-collapse-item title="Telegram Bot" name="telegram">
                <p class="trigger-desc">通过 Telegram Bot 交互式管理设备，支持查看状态、开关机、扫描局域网、查看日志等功能。</p>
                <h4>配置步骤</h4>
                <ol>
                  <li>在 Telegram 中搜索 <a href="https://t.me/BotFather" target="_blank" style="color:#007AFF">@BotFather</a>，发送 <code>/newbot</code> 创建 Bot</li>
                  <li>获取 Bot Token（格式如 <code>123456:ABC-DEF...</code>）</li>
                  <li>在「触发源管理」中添加 Telegram 类型的触发源，填入 Token</li>
                  <li>（可选）填写允许的 Chat ID 限制访问权限</li>
                  <li>在 Telegram 中搜索你的 Bot 并发送 <code>/start</code></li>
                </ol>
                <h4>可用命令</h4>
                <div class="code-block">
                  <code>/start — 显示主菜单 &nbsp;|&nbsp; /devices — 查看设备并开关机<br/>/groups — 设备分组 &nbsp;|&nbsp; /scan — 扫描局域网 &nbsp;|&nbsp; /logs — 操作日志</code>
                </div>
                <p class="trigger-tip">Chat ID 可通过向 <a href="https://t.me/userinfobot" target="_blank" style="color:#007AFF">@userinfobot</a> 发消息获取，多个用逗号分隔。留空则不限制访问。</p>
              </n-collapse-item>
            </n-collapse>
          </div>
        </n-tab-pane>

        <n-tab-pane name="api" tab="API 手册">
          <div class="section">
            <p class="trigger-desc">Wol_xyz 提供完整的 RESTful API，支持 Swagger UI 和 ReDoc 两种交互式文档。</p>

            <h4>打开 API 文档</h4>
            <div class="code-block">
              <div class="code-label">Swagger UI（交互式测试）</div>
              <code>http://&lt;服务器IP&gt;:39090/docs</code>
            </div>
            <div class="code-block">
              <div class="code-label">ReDoc（阅读友好）</div>
              <code>http://&lt;服务器IP&gt;:39090/redoc</code>
            </div>
            <div class="code-block">
              <div class="code-label">OpenAPI JSON（供程序消费）</div>
              <code>http://&lt;服务器IP&gt;:39090/openapi.json</code>
            </div>

            <n-divider />

            <h4>主要接口一览</h4>
            <n-table :bordered="false" :single-line="false" size="small" style="font-size:13px">
              <thead><tr><th>路径前缀</th><th>说明</th><th>认证</th></tr></thead>
              <tbody>
                <tr><td><code>/api/auth</code></td><td>登录、用户信息、修改密码</td><td>登录接口公开</td></tr>
                <tr><td><code>/api/devices</code></td><td>设备增删改查、开机、关机</td><td>JWT</td></tr>
                <tr><td><code>/api/groups</code></td><td>设备分组管理</td><td>JWT</td></tr>
                <tr><td><code>/api/schedules</code></td><td>定时任务管理</td><td>JWT</td></tr>
                <tr><td><code>/api/channels</code></td><td>通知渠道管理</td><td>JWT</td></tr>
                <tr><td><code>/api/triggers</code></td><td>触发源管理</td><td>JWT</td></tr>
                <tr><td><code>/api/external/trigger</code></td><td>外部触发（Token 认证）</td><td>Token</td></tr>
                <tr><td><code>/api/logs</code></td><td>操作日志</td><td>JWT</td></tr>
                <tr><td><code>/api/scan</code></td><td>局域网扫描</td><td>JWT</td></tr>
                <tr><td><code>/ws/status</code></td><td>设备状态 WebSocket 推送</td><td>无</td></tr>
              </tbody>
            </n-table>
            <p class="trigger-tip">所有需要 JWT 认证的接口需在请求头携带 <code>Authorization: Bearer &lt;token&gt;</code>，Token 通过 <code>POST /api/auth/login</code> 获取。</p>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>
  </n-modal>
</template>

<style scoped>
.guide-content {
  line-height: 1.8;
  font-size: 14px;
  color: #555;
}
.section {
  padding: 4px 0;
}
.guide-content h3 {
  color: #1c1c1e;
  font-size: 16px;
  margin: 0 0 8px;
}
.guide-content h4 {
  color: #1c1c1e;
  font-size: 14px;
  margin: 12px 0 6px;
}
.guide-content ol {
  padding-left: 20px;
  margin: 4px 0 8px;
}
.trigger-desc {
  color: #666;
  margin: 0 0 10px;
}
.code-block {
  background: rgba(0, 0, 0, 0.04);
  border-radius: 10px;
  padding: 10px 14px;
  margin: 8px 0;
}
.code-block .code-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
  font-weight: 500;
}
.code-block code {
  font-size: 12px;
  color: #1c1c1e;
  word-break: break-all;
  font-family: 'SF Mono', SFMono-Regular, Menlo, monospace;
}
.trigger-tip {
  font-size: 12px;
  color: #999;
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(0, 122, 255, 0.05);
  border-radius: 8px;
  border-left: 3px solid #007AFF;
}
.trigger-tip code {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
