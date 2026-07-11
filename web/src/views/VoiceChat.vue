<template>
  <div class="voice-chat">
    <div class="voice-container">
      <!-- 语音波形动画 -->
      <div class="voice-wave" :class="{ active: isListening || isSpeaking }">
        <div class="wave-bar" v-for="i in 5" :key="i"></div>
      </div>

      <!-- 状态显示 -->
      <div class="status-text">
        <span v-if="!isListening && !isSpeaking">点击麦克风开始对话</span>
        <span v-if="isListening" class="listening">🎤 正在听...</span>
        <span v-if="isSpeaking" class="speaking">🔊 正在播报...</span>
      </div>

      <!-- 麦克风按钮 -->
      <button
        class="mic-button"
        :class="{ active: isListening, disabled: isSpeaking }"
        @click="toggleListening"
        :disabled="isSpeaking"
      >
        <i class="el-icon-microphone"></i>
      </button>

      <!-- 实时识别的文字 -->
      <div class="recognized-text" v-if="recognizedText">
        <p class="label">你说：</p>
        <p class="text">{{ recognizedText }}</p>
      </div>

      <!-- AI响应 -->
      <div class="ai-response" v-if="aiResponse">
        <p class="label">AI助手：</p>
        <p class="text">{{ aiResponse }}</p>
      </div>

      <!-- 对话历史 -->
      <div class="conversation-history">
        <div
          v-for="(msg, index) in conversationHistory"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">
            <span class="role-label">{{ msg.role === 'user' ? '你' : 'AI' }}：</span>
            <span class="text">{{ msg.content }}</span>
          </div>
          <div class="message-time">{{ msg.time }}</div>
        </div>
      </div>
    </div>

    <!-- 设置面板 -->
    <div class="settings">
      <el-switch v-model="autoSpeak" active-text="AI语音播报"></el-switch>
      <el-switch v-model="continuous" active-text="连续对话模式"></el-switch>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const isListening = ref(false)
const isSpeaking = ref(false)
const recognizedText = ref('')
const aiResponse = ref('')
const conversationHistory = ref([])
const autoSpeak = ref(true)  // 自动语音播报
const continuous = ref(false) // 连续对话模式

let recognition = null
let synthesis = null

// 初始化语音识别
onMounted(() => {
  initSpeechRecognition()
  initSpeechSynthesis()
})

// 初始化Web Speech API - 语音识别
function initSpeechRecognition() {
  if (!('webkitSpeechRecognition' in window)) {
    ElMessage.warning('你的浏览器不支持语音识别，请使用Chrome浏览器')
    return
  }

  recognition = new webkitSpeechRecognition()
  recognition.lang = 'zh-CN'  // 中文
  recognition.continuous = false  // 单次识别
  recognition.interimResults = true  // 实时结果

  recognition.onstart = () => {
    isListening.value = true
    recognizedText.value = ''
  }

  recognition.onresult = (event) => {
    let interimTranscript = ''
    let finalTranscript = ''

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        finalTranscript += transcript
      } else {
        interimTranscript += transcript
      }
    }

    recognizedText.value = finalTranscript || interimTranscript

    // 如果是最终结果，发送给AI
    if (finalTranscript) {
      sendToAI(finalTranscript)
    }
  }

  recognition.onerror = (event) => {
    console.error('语音识别错误:', event.error)
    isListening.value = false
    
    if (event.error === 'no-speech') {
      ElMessage.warning('没有检测到语音，请重试')
    } else if (event.error === 'not-allowed') {
      ElMessage.error('请允许浏览器使用麦克风')
    }
  }

  recognition.onend = () => {
    isListening.value = false
    
    // 连续模式：自动重启识别
    if (continuous.value && !isSpeaking.value) {
      setTimeout(() => {
        startListening()
      }, 500)
    }
  }
}

// 初始化语音合成
function initSpeechSynthesis() {
  if (!('speechSynthesis' in window)) {
    ElMessage.warning('你的浏览器不支持语音播报')
    return
  }
  
  synthesis = window.speechSynthesis
}

// 开始/停止监听
function toggleListening() {
  if (isListening.value) {
    stopListening()
  } else {
    startListening()
  }
}

function startListening() {
  if (recognition) {
    recognition.start()
  }
}

function stopListening() {
  if (recognition) {
    recognition.stop()
    isListening.value = false
  }
}

// 发送给AI处理
async function sendToAI(text) {
  // 添加到历史
  addToHistory('user', text)

  try {
    // 调用AI接口
    const response = await api.post('/chat', {
      message: text,
      mode: 'voice'  // 标记为语音模式，AI会更口语化
    })

    const aiText = response.data.response
    aiResponse.value = aiText
    addToHistory('assistant', aiText)

    // 自动语音播报
    if (autoSpeak.value) {
      speak(aiText)
    }

  } catch (error) {
    console.error('AI处理失败:', error)
    const errorMsg = '抱歉，我没听懂，能再说一遍吗？'
    aiResponse.value = errorMsg
    addToHistory('assistant', errorMsg)
    
    if (autoSpeak.value) {
      speak(errorMsg)
    }
  }
}

// 语音播报
function speak(text) {
  if (!synthesis) return

  // 停止之前的播报
  synthesis.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'zh-CN'
  utterance.rate = 1.0  // 语速
  utterance.pitch = 1.0  // 音调
  utterance.volume = 1.0  // 音量

  utterance.onstart = () => {
    isSpeaking.value = true
  }

  utterance.onend = () => {
    isSpeaking.value = false
  }

  utterance.onerror = (event) => {
    console.error('语音播报错误:', event)
    isSpeaking.value = false
  }

  synthesis.speak(utterance)
}

// 添加到历史记录
function addToHistory(role, content) {
  conversationHistory.value.push({
    role,
    content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  // 限制历史记录数量
  if (conversationHistory.value.length > 20) {
    conversationHistory.value.shift()
  }
}

// 清理
onUnmounted(() => {
  if (recognition) {
    recognition.stop()
  }
  if (synthesis) {
    synthesis.cancel()
  }
})
</script>

<style scoped>
.voice-chat {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.voice-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  color: white;
  box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

/* 语音波形动画 */
.voice-wave {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
  height: 80px;
  margin-bottom: 20px;
}

.wave-bar {
  width: 4px;
  height: 20px;
  background: rgba(255,255,255,0.3);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.voice-wave.active .wave-bar {
  animation: wave 0.8s ease-in-out infinite;
}

.voice-wave.active .wave-bar:nth-child(1) { animation-delay: 0s; }
.voice-wave.active .wave-bar:nth-child(2) { animation-delay: 0.1s; }
.voice-wave.active .wave-bar:nth-child(3) { animation-delay: 0.2s; }
.voice-wave.active .wave-bar:nth-child(4) { animation-delay: 0.1s; }
.voice-wave.active .wave-bar:nth-child(5) { animation-delay: 0s; }

@keyframes wave {
  0%, 100% { height: 20px; }
  50% { height: 60px; }
}

/* 状态文字 */
.status-text {
  font-size: 18px;
  margin-bottom: 30px;
  min-height: 30px;
}

.listening {
  color: #ffd700;
  font-weight: bold;
  animation: pulse 1.5s ease-in-out infinite;
}

.speaking {
  color: #90EE90;
  font-weight: bold;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 麦克风按钮 */
.mic-button {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: none;
  background: white;
  color: #667eea;
  font-size: 48px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 5px 20px rgba(0,0,0,0.2);
}

.mic-button:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

.mic-button.active {
  background: #ff4444;
  color: white;
  animation: mic-pulse 1s ease-in-out infinite;
}

.mic-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes mic-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 识别文字和AI响应 */
.recognized-text,
.ai-response {
  margin-top: 30px;
  padding: 20px;
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  backdrop-filter: blur(10px);
}

.label {
  font-size: 14px;
  opacity: 0.8;
  margin-bottom: 10px;
}

.text {
  font-size: 18px;
  line-height: 1.6;
}

/* 对话历史 */
.conversation-history {
  margin-top: 40px;
  max-height: 300px;
  overflow-y: auto;
  text-align: left;
}

.message {
  margin-bottom: 15px;
  padding: 15px;
  border-radius: 10px;
  animation: fadeIn 0.3s ease;
}

.message.user {
  background: rgba(255,255,255,0.15);
  margin-left: 20px;
}

.message.assistant {
  background: rgba(255,255,255,0.25);
  margin-right: 20px;
}

.message-content {
  margin-bottom: 5px;
}

.role-label {
  font-weight: bold;
  margin-right: 8px;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
  text-align: right;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 设置面板 */
.settings {
  margin-top: 30px;
  padding: 20px;
  background: white;
  border-radius: 10px;
  display: flex;
  justify-content: space-around;
  align-items: center;
}
</style>
