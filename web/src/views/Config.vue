<template>
  <div class="config">
    <el-card>
      <template #header>
        <div class="header">
          <span>配置管理</span>
          <el-button type="primary" @click="saveConfig" :loading="saving" :icon="Check">
            保存配置
          </el-button>
        </div>
      </template>

      <el-form :model="config" label-width="150px" v-loading="loading">
        <el-divider content-position="left">飞书配置</el-divider>
        <el-form-item label="App ID">
          <SensitiveInput v-model="config.FEISHU_APP_ID" placeholder="cli_xxxxxxxxxxxxxxxx" />
        </el-form-item>
        <el-form-item label="App Secret">
          <SensitiveInput v-model="config.FEISHU_APP_SECRET" placeholder="请输入App Secret" />
        </el-form-item>
        <el-form-item label="群组ID">
          <SensitiveInput v-model="config.FEISHU_CHAT_ID" placeholder="oc_xxxxxxxxxxxxxxxx" />
        </el-form-item>

        <el-divider content-position="left">AI配置</el-divider>
        <el-form-item label="API Key">
          <SensitiveInput v-model="config.AI_API_KEY" placeholder="sk-xxxxxxxxxxxxxxxx" />
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="config.AI_API_BASE" placeholder="https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="config.AI_MODEL" placeholder="deepseek-chat" />
        </el-form-item>

        <el-divider content-position="left">邮件配置</el-divider>
        <el-form-item label="SMTP服务器">
          <el-input v-model="config.SMTP_HOST" placeholder="smtp.163.com" />
        </el-form-item>
        <el-form-item label="SMTP端口">
          <el-input-number v-model.number="config.SMTP_PORT" :min="1" :max="65535" placeholder="465" />
        </el-form-item>
        <el-form-item label="SMTP用户名">
          <el-input v-model="config.SMTP_USER" placeholder="your_email@163.com" />
        </el-form-item>
        <el-form-item label="SMTP密码">
          <SensitiveInput v-model="config.SMTP_PASSWORD" placeholder="授权码或密码" />
        </el-form-item>
        <el-form-item label="业务负责人邮箱">
          <el-input v-model="config.BUSINESS_EMAILS" placeholder="多个邮箱用逗号分隔" />
          <div class="hint">无异常时接收日报</div>
        </el-form-item>
        <el-form-item label="技术运维邮箱">
          <el-input v-model="config.TECH_EMAILS" placeholder="多个邮箱用逗号分隔" />
          <div class="hint">有异常时接收告警</div>
        </el-form-item>

        <el-divider content-position="left">企业微信配置</el-divider>
        <el-form-item label="Webhook URL">
          <SensitiveInput v-model="config.WECOM_WEBHOOK" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" />
          <div class="hint">可选：企业微信群机器人Webhook地址</div>
        </el-form-item>

        <el-divider content-position="left">系统配置</el-divider>
        <el-form-item label="报告输出目录">
          <el-input v-model="config.REPORT_OUTPUT_DIR" placeholder="./reports" />
        </el-form-item>
        <el-form-item label="定时任务时间">
          <el-row :gutter="8">
            <el-col :span="12">
              <el-input-number v-model.number="config.DAILY_RUN_HOUR" :min="0" :max="23" placeholder="小时" style="width: 100%;" />
            </el-col>
            <el-col :span="12">
              <el-input-number v-model.number="config.DAILY_RUN_MINUTE" :min="0" :max="59" placeholder="分钟" style="width: 100%;" />
            </el-col>
          </el-row>
          <div class="hint">每天自动执行的时间（小时:分钟）</div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { getConfig, saveConfig as saveConfigApi } from '../api'
import SensitiveInput from '../components/SensitiveInput.vue'

const config = ref({
  FEISHU_APP_ID: '',
  FEISHU_APP_SECRET: '',
  FEISHU_CHAT_ID: '',
  SMTP_HOST: '',
  SMTP_PORT: 465,
  SMTP_USER: '',
  SMTP_PASSWORD: '',
  BUSINESS_EMAILS: '',
  TECH_EMAILS: '',
  AI_API_KEY: '',
  AI_API_BASE: '',
  AI_MODEL: '',
  WECOM_WEBHOOK: '',
  REPORT_OUTPUT_DIR: '',
  DAILY_RUN_HOUR: 20,
  DAILY_RUN_MINUTE: 0
})
const loading = ref(false)
const saving = ref(false)

const loadConfig = async () => {
  loading.value = true
  try {
    const res = await getConfig()
    Object.assign(config.value, res.data)
  } catch (error) {
    ElMessage.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    await saveConfigApi(config.value)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('保存配置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.config {
  max-width: 800px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}
</style>
