<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <el-icon :size="40" :color="healthStatus.feishu ? '#52c41a' : '#ff4d4f'">
              <ChatLineRound />
            </el-icon>
            <div class="info">
              <div class="label">飞书配置</div>
              <div class="value">{{ healthStatus.feishu ? '已配置' : '未配置' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <el-icon :size="40" :color="healthStatus.ai ? '#52c41a' : '#ff4d4f'">
              <Cpu />
            </el-icon>
            <div class="info">
              <div class="label">AI配置</div>
              <div class="value">{{ healthStatus.ai ? '已配置' : '未配置' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <el-icon :size="40" :color="healthStatus.email ? '#52c41a' : '#ff4d4f'">
              <Message />
            </el-icon>
            <div class="info">
              <div class="label">邮件配置</div>
              <div class="value">{{ healthStatus.email ? '已配置' : '未配置' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="card-content">
            <el-icon :size="40" :color="healthStatus.wecom ? '#52c41a' : '#8c8c8c'">
              <ChatDotRound />
            </el-icon>
            <div class="info">
              <div class="label">企业微信</div>
              <div class="value">{{ healthStatus.wecom ? '已配置' : '未配置' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <el-space direction="vertical" style="width: 100%;" :size="12">
            <el-button type="primary" :icon="ChatDotRound" @click="goToChat" style="width: 100%;">
              智能对话分析（推荐）
            </el-button>
            <el-button :icon="Search" @click="goToAnalysis" style="width: 100%;">
              表单式分析
            </el-button>
            <el-button :icon="Document" @click="goToReports" style="width: 100%;">
              查看历史报告
            </el-button>
            <el-button :icon="Setting" @click="goToConfig" style="width: 100%;">
              配置管理
            </el-button>
          </el-space>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="飞书群组">{{ chatId || '未配置' }}</el-descriptions-item>
            <el-descriptions-item label="AI模型">{{ aiModel || '未配置' }}</el-descriptions-item>
            <el-descriptions-item label="报告目录">{{ reportDir || './reports' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Document, Setting, ChatDotRound } from '@element-plus/icons-vue'
import { getHealth } from '../api'

const router = useRouter()
const healthStatus = ref({ feishu: false, ai: false, email: false, wecom: false })
const chatId = ref('')
const aiModel = ref('')
const reportDir = ref('')

const loadHealth = async () => {
  try {
    const res = await getHealth()
    healthStatus.value = res.data.services
    chatId.value = res.data.chat_id
    aiModel.value = res.data.ai_model
    reportDir.value = res.data.report_dir
  } catch (error) {
    ElMessage.error('获取系统状态失败')
  }
}

const goToChat = () => router.push('/chat')
const goToAnalysis = () => router.push('/analysis')
const goToReports = () => router.push('/reports')
const goToConfig = () => router.push('/config')

onMounted(() => {
  loadHealth()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.status-card {
  height: 120px;
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.info {
  flex: 1;
}

.label {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.value {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}
</style>
