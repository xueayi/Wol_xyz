<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ show: boolean }>()
const emit = defineEmits(['update:show'])

const triggerTab = ref('http')
</script>

<template>
  <n-modal :show="show" @update:show="emit('update:show', $event)" preset="card"
    title="使用指引" style="width: 660px" :bordered="false">
    <div class="guide-content">
      <h3>快速开始</h3>
      <ol>
        <li><b>添加设备</b>：点击「手动添加」或「扫描局域网」发现设备</li>
        <li><b>分组管理</b>：在设备概览区管理设备分组归属</li>
        <li><b>远程开机</b>：点击设备卡片上的「开机」按钮发送 WOL 魔术包</li>
        <li><b>远程关机</b>：先在设备配置中启用并填写 SSH 信息</li>
        <li><b>定时任务</b>：设置 Cron 表达式自动执行开关机</li>
        <li><b>通知渠道</b>：配置邮件或 Webhook 接收操作通知</li>
      </ol>

      <n-divider />

      <h3 style="margin-bottom: 12px">外部触发源</h3>
      <n-tabs v-model:value="triggerTab" type="segment" animated>
        <n-tab-pane name="http" tab="HTTP API">
          <div class="trigger-section">
            <p class="trigger-desc">通过带 Token 的 HTTP 请求触发设备开关机，适用于脚本、自动化工具或第三方平台调用。</p>
            <h4>配置步骤</h4>
            <ol>
              <li>在「触发源管理」中添加 HTTP API 类型的触发源</li>
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
          </div>
        </n-tab-pane>

        <n-tab-pane name="bemfa" tab="巴法云">
          <div class="trigger-section">
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
          </div>
        </n-tab-pane>

        <n-tab-pane name="mqtt" tab="MQTT">
          <div class="trigger-section">
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
              <code>Topic: xiaoxue_wol/device1 &nbsp; Payload: on</code>
            </div>
            <div class="code-block">
              <div class="code-label">关机</div>
              <code>Topic: xiaoxue_wol/device1 &nbsp; Payload: off</code>
            </div>
            <div class="code-block">
              <div class="code-label">mosquitto_pub 示例</div>
              <code>mosquitto_pub -h &lt;BROKER_IP&gt; -t "xiaoxue_wol/device1" -m "on"</code>
            </div>
            <p class="trigger-tip">Payload 仅需发送 <code>on</code>（开机）或 <code>off</code>（关机），不区分大小写</p>
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
.trigger-section {
  padding: 4px 0;
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
