<template>
  <div class="chat">
    <el-card class="chat-container">
      <template #header>
        <div class="header">
          <span>智能对话分析</span>
          <el-button :icon="Delete" @click="clearChat" text>清空对话</el-button>
        </div>
      </template>

      <div class="messages-container" ref="messagesContainer">
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading" :size="40" color="#409eff"><Loading /></el-icon>
          <p>加载历史记录中...</p>
        </div>

        <div v-else-if="messages.length === 0" class="empty-state">
          <el-icon :size="60" color="#d9d9d9"><ChatDotRound /></el-icon>
          <p>试试直接问我吧！例如：</p>
          <ul>
            <li>"分析今天下午2点后的RPA日志"</li>
            <li>"帮我配置飞书，App ID是cli_xxx，App Secret是xxx"</li>
            <li>"从数据库查询今天的RPA记录"</li>
            <li>"把这次分析保存为模板，名称是生产环境日报"</li>
          </ul>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.role]"
        >
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
            <el-icon v-else :size="24"><Cpu /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">{{ msg.role === 'user' ? '你' : 'AI助手' }}</span>
              <span class="message-time">{{ msg.time }}</span>
            </div>
            <div class="message-text">
              <div v-if="msg.loading" class="loading-dots">
                <span></span><span></span><span></span>
              </div>
              <pre v-else>{{ msg.content }}</pre>
            </div>
            <div v-if="msg.report_file" class="message-attachment">
              <el-tag type="success">
                <el-icon><Document /></el-icon>
                {{ msg.report_file }}
              </el-tag>
              <el-button type="primary" link :icon="Download" @click="downloadReport(msg.report_file)">
                下载报告
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="input-container">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="试试问我：'分析今天下午的RPA日志' 或 '看看昨天的运行情况'"
          @keydown.enter.ctrl="sendMessage"
          :disabled="analyzing"
        />
        <div class="input-actions">
          <span class="hint">Ctrl + Enter 发送</span>
          <el-button type="primary" @click="sendMessage" :loading="analyzing" :icon="Promotion">
            发送
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card class="suggestions-card">
      <template #header>
        <span>快速提问</span>
      </template>
      <el-space wrap>
        <el-tag
          v-for="(suggestion, index) in suggestions"
          :key="index"
          @click="quickAsk(suggestion)"
          class="suggestion-tag"
          type="info"
        >
          {{ suggestion }}
        </el-tag>
      </el-space>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, User, Cpu, Document, Download, Promotion, ChatDotRound, Loading } from '@element-plus/icons-vue'
import { analyzeLog, getReportDownloadUrl, getSessionHistory } from '../api'

const messages = ref([])
const inputText = ref('')
const analyzing = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(localStorage.getItem('current_session_id') || generateSessionId())
const loading = ref(false)

// 生成新的会话ID
function generateSessionId() {
  const id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  localStorage.setItem('current_session_id', id)
  return id
}

// 加载历史对话记录
const loadHistory = async () => {
  loading.value = true
  try {
    const res = await getSessionHistory(sessionId.value)
    if (res.data.success && res.data.messages && res.data.messages.length > 0) {
      // 将数据库记录转换为前端消息格式
      messages.value = []
      res.data.messages.forEach(msg => {
        // 用户消息
        messages.value.push({
          role: 'user',
          content: msg.user_message,
          time: formatTime(msg.created_at)
        })
        // AI回复
        messages.value.push({
          role: 'assistant',
          content: msg.ai_response,
          time: formatTime(msg.created_at),
          report_file: msg.report_file
        })
      })
      scrollToBottom()
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    // 失败不提示，保持静默
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return getCurrentTime()
  const date = new Date(timestamp)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistory()
})

const suggestions = [
  '分析今天的RPA日志',
  '看看今天下午2点后的日志',
  '帮我配置飞书App ID',
  '把这次分析保存为模板',
  '使用生产环境模板分析',
  '从数据库查询今天的RPA记录'
]

const getCurrentTime = () => {
  const now = new Date()
  return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!inputText.value.trim() || analyzing.value) return

  const userMessage = {
    role: 'user',
    content: inputText.value.trim(),
    time: getCurrentTime()
  }

  messages.value.push(userMessage)
  scrollToBottom()

  const userQuery = inputText.value.trim()
  inputText.value = ''

  // AI正在思考
  const aiMessage = {
    role: 'assistant',
    content: '',
    time: getCurrentTime(),
    loading: true
  }
  messages.value.push(aiMessage)
  scrollToBottom()

  analyzing.value = true

  try {
    // 调用后端API，传入自然语言查询
    const res = await analyzeLog({
      query_text: userQuery,  // 字段名必须是query_text，对应后端AnalysisRequest模型
      start_date: '',  // 留空，让Agent自动识别
      end_date: '',
      start_time: '',
      end_time: '',
      session_id: sessionId.value  // 传入会话ID
    })

    aiMessage.loading = false
    // 后端返回的字段是result，不是summary
    aiMessage.content = res.data.result || res.data.summary || '分析完成'

    // 更新sessionId（后端可能生成新的）
    if (res.data.session_id) {
      sessionId.value = res.data.session_id
      localStorage.setItem('current_session_id', res.data.session_id)
    }

    if (res.data.report_file) {
      aiMessage.report_file = res.data.report_file
    }
    scrollToBottom()

    ElMessage.success('分析完成')
  } catch (error) {
    aiMessage.loading = false
    aiMessage.content = '抱歉，分析失败了：' + (error.response?.data?.detail || error.message)
    scrollToBottom()
    ElMessage.error('分析失败')
  } finally {
    analyzing.value = false
  }
}

const quickAsk = (question) => {
  inputText.value = question
  sendMessage()
}

const clearChat = async () => {
  try {
    // 先清空前端显示
    messages.value = []

    // 如果有历史记录，清空数据库中的会话
    const { clearSession } = await import('../api')
    await clearSession(sessionId.value)

    // 生成新的会话ID
    sessionId.value = generateSessionId()

    ElMessage.success('对话已清空')
  } catch (error) {
    console.error('清空对话失败:', error)
    // 即使数据库清空失败，前端也已经清空了
    sessionId.value = generateSessionId()
  }
}

const downloadReport = (filename) => {
  window.open(getReportDownloadUrl(filename), '_blank')
}
</script>

<style scoped>
.chat {
  max-width: 1200px;
  display: flex;
  gap: 16px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 600px;
}

.chat-container :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #8c8c8c;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
  color: #409eff;
}

.loading-state p {
  margin-top: 20px;
  font-size: 16px;
}

.empty-state p {
  margin: 20px 0 10px;
  font-size: 16px;
}

.empty-state ul {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 14px;
}

.empty-state li {
  padding: 8px 0;
  color: #1890ff;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message.user .message-avatar {
  background-color: #1890ff;
  color: #fff;
}

.message.assistant .message-avatar {
  background-color: #52c41a;
  color: #fff;
}

.message-content {
  max-width: 70%;
  min-width: 200px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message.user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-weight: 600;
  font-size: 14px;
  color: #262626;
}

.message-time {
  font-size: 12px;
  color: #8c8c8c;
}

.message-text {
  background-color: #fff;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message.user .message-text {
  background-color: #1890ff;
  color: #fff;
}

.message-text pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #8c8c8c;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-attachment {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-container {
  padding: 16px;
  background-color: #fff;
  border-top: 1px solid #f0f0f0;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  font-size: 12px;
  color: #8c8c8c;
}

.suggestions-card {
  width: 280px;
  height: fit-content;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.suggestion-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>
