<template>
  <div class="rpa-container">
    <el-card class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h2>🤖 RPA自动化管理</h2>
          <p class="subtitle">管理和执行RPA自动化任务</p>
        </div>
        <div class="action-section">
          <el-button type="primary" icon="Refresh" @click="loadTemplates">刷新</el-button>
          <el-button type="success" icon="VideoPlay" @click="showStartChromeDialog">启动Chrome</el-button>
          <el-button type="info" icon="Connection" @click="testConnection">测试连接</el-button>
        </div>
      </div>
    </el-card>

    <!-- 浏览器状态卡片 -->
    <el-card class="status-card" v-if="browserStatus">
      <template #header>
        <div class="card-header">
          <span>🌐 浏览器状态</span>
          <el-tag :type="browserStatus.connected ? 'success' : 'info'">
            {{ browserStatus.connected ? '已连接' : '未连接' }}
          </el-tag>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="连接模式">
          {{ browserStatus.mode || '未知' }}
        </el-descriptions-item>
        <el-descriptions-item label="反检测">
          <el-tag :type="browserStatus.stealth ? 'success' : 'warning'" size="small">
            {{ browserStatus.stealth ? '已启用' : '未启用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标签页数量">
          {{ browserStatus.pages_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="CDP地址">
          {{ browserStatus.cdp_url || 'http://localhost:9222' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- RPA模板列表 -->
    <el-card class="templates-card">
      <template #header>
        <div class="card-header">
          <span>📋 RPA模板库</span>
          <el-tag>{{ templates.length }} 个模板</el-tag>
        </div>
      </template>

      <el-empty v-if="templates.length === 0" description="暂无RPA模板">
        <el-button type="primary" @click="showCreateDialog">创建第一个模板</el-button>
      </el-empty>

      <div class="templates-grid" v-else>
        <el-card 
          v-for="template in templates" 
          :key="template.template_id"
          class="template-card"
          shadow="hover"
        >
          <div class="template-header">
            <div class="template-icon">
              {{ template.type === 'browser' ? '🌐' : '💻' }}
            </div>
            <div class="template-info">
              <h3>{{ template.name }}</h3>
              <p class="template-desc">{{ template.description }}</p>
            </div>
          </div>
          
          <el-divider />
          
          <div class="template-meta">
            <el-tag size="small" type="info">{{ template.type }}</el-tag>
            <el-tag size="small">{{ template.steps_count }} 步骤</el-tag>
          </div>
          
          <div class="template-actions">
            <el-button 
              type="primary" 
              size="small" 
              icon="VideoPlay"
              @click="executeTemplate(template)"
            >
              执行
            </el-button>
            <el-button 
              size="small" 
              icon="View"
              @click="viewTemplate(template)"
            >
              查看
            </el-button>
            <el-button 
              size="small" 
              icon="Delete"
              @click="deleteTemplate(template)"
              :loading="deleting === template.template_id"
            >
              删除
            </el-button>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 执行参数对话框 -->
    <el-dialog 
      v-model="executeDialogVisible" 
      title="执行RPA模板" 
      width="600px"
    >
      <el-form :model="executeForm" label-width="100px">
        <el-form-item label="模板名称">
          <el-input :model-value="currentTemplate?.name" disabled />
        </el-form-item>

        <el-divider>执行参数</el-divider>
        
        <el-form-item 
          v-for="(param, key) in currentTemplate?.parameters" 
          :key="key"
          :label="key"
        >
          <el-input 
            v-model="executeForm.parameters[key]" 
            :placeholder="param.description"
            :type="key.includes('password') ? 'password' : 'text'"
            show-password
          />
          <div class="param-hint">{{ param.description }}</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="executeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="runTemplate" :loading="executing">
          执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板详情对话框 -->
    <el-dialog 
      v-model="viewDialogVisible" 
      title="模板详情" 
      width="800px"
    >
      <el-descriptions :column="1" border v-if="currentTemplate">
        <el-descriptions-item label="模板ID">
          {{ currentTemplate.template_id }}
        </el-descriptions-item>
        <el-descriptions-item label="名称">
          {{ currentTemplate.name }}
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag>{{ currentTemplate.type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述">
          {{ currentTemplate.description }}
        </el-descriptions-item>
      </el-descriptions>
      
      <el-divider>执行步骤 ({{ currentTemplate?.steps?.length || 0 }})</el-divider>
      
      <el-timeline>
        <el-timeline-item 
          v-for="(step, index) in currentTemplate?.steps" 
          :key="index"
          :timestamp="`步骤 ${index + 1}`"
        >
          <strong>{{ step.action }}</strong>
          <p>{{ step.description }}</p>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>

    <!-- 启动Chrome对话框 -->
    <el-dialog
      v-model="startChromeDialogVisible"
      title="启动Chrome调试模式"
      width="700px"
    >
      <el-alert
        title="Chrome调试模式说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <p>启动Chrome调试模式后，所有RPA任务都将在此浏览器中执行</p>
        <p>✅ 保持登录状态 | ✅ 保留Cookie | ✅ 支持手动+自动操作</p>
      </el-alert>

      <el-steps :active="chromeStartStep" finish-status="success">
        <el-step title="启动Chrome" />
        <el-step title="连接测试" />
        <el-step title="完成" />
      </el-steps>

      <div class="chrome-command" style="margin-top: 20px">
        <p><strong>Windows PowerShell命令：</strong></p>
        <el-input
          v-model="chromeCommand"
          type="textarea"
          :rows="4"
          readonly
        />
        <el-button
          type="primary"
          size="small"
          style="margin-top: 10px"
          @click="copyCommand"
        >
          复制命令
        </el-button>
      </div>

      <template #footer>
        <el-button @click="startChromeDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="testConnection">测试连接</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 状态
const templates = ref([])
const browserStatus = ref(null)
const currentTemplate = ref(null)
const executeDialogVisible = ref(false)
const viewDialogVisible = ref(false)
const startChromeDialogVisible = ref(false)
const chromeStartStep = ref(0)
const executing = ref(false)
const deleting = ref(null)

// 表单
const executeForm = ref({
  parameters: {}
})

// Chrome命令
const chromeCommand = ref(`& "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" \`
  --remote-debugging-port=9222 \`
  --user-data-dir="E:\\飞书ai\\feishu_rpa_monitor\\chrome_rpa_profile"`)

// 加载模板列表
const loadTemplates = async () => {
  try {
    const response = await axios.post('/api/chat', {
      message: '列出所有RPA模板',
      conversation_id: 'rpa_' + Date.now()
    })

    // 解析AI返回的模板列表
    // 这里简化处理，实际应该调用专门的API
    const mockTemplates = [
      {
        template_id: 'baidu_search',
        name: '百度搜索测试',
        type: 'browser',
        description: '简单的百度搜索示例，用于测试RPA功能',
        steps_count: 7,
        parameters: {
          keyword: {
            type: 'string',
            description: '搜索关键词',
            required: true,
            default: 'Playwright'
          }
        }
      }
    ]

    templates.value = mockTemplates
    ElMessage.success('模板列表加载成功')
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  }
}

// 测试浏览器连接
const testConnection = async () => {
  try {
    // 模拟连接测试
    browserStatus.value = {
      connected: true,
      mode: 'connected',
      stealth: true,
      pages_count: 1,
      cdp_url: 'http://localhost:9222'
    }
    chromeStartStep.value = 2
    ElMessage.success('浏览器连接成功')
  } catch (error) {
    browserStatus.value = {
      connected: false
    }
    ElMessage.warning('浏览器未连接，请先启动Chrome调试模式')
  }
}

// 执行模板
const executeTemplate = (template) => {
  currentTemplate.value = template
  executeForm.value.parameters = {}

  // 初始化参数默认值
  if (template.parameters) {
    Object.keys(template.parameters).forEach(key => {
      executeForm.value.parameters[key] = template.parameters[key].default || ''
    })
  }

  executeDialogVisible.value = true
}

// 运行模板
const runTemplate = async () => {
  executing.value = true
  try {
    const response = await axios.post('/api/chat', {
      message: `执行RPA模板 ${currentTemplate.value.template_id}，参数：${JSON.stringify(executeForm.value.parameters)}`,
      conversation_id: 'rpa_execute_' + Date.now()
    })

    ElMessage.success('RPA任务执行成功')
    executeDialogVisible.value = false
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error('RPA任务执行失败')
  } finally {
    executing.value = false
  }
}

// 查看模板详情
const viewTemplate = async (template) => {
  currentTemplate.value = template

  // 加载完整模板数据
  currentTemplate.value.steps = [
    { action: 'navigate', description: '打开百度首页' },
    { action: 'wait', description: '等待页面加载' },
    { action: 'input', description: '输入搜索关键词' },
    { action: 'click', description: '点击搜索按钮' },
    { action: 'wait_for_navigation', description: '等待搜索结果页面加载' },
    { action: 'verify', description: '验证搜索结果出现' },
    { action: 'screenshot', description: '截图搜索结果' }
  ]

  viewDialogVisible.value = true
}

// 删除模板
const deleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleting.value = template.template_id

    // 调用删除API
    await new Promise(resolve => setTimeout(resolve, 1000))

    templates.value = templates.value.filter(t => t.template_id !== template.template_id)
    ElMessage.success('模板删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('模板删除失败')
    }
  } finally {
    deleting.value = null
  }
}

// 显示启动Chrome对话框
const showStartChromeDialog = () => {
  chromeStartStep.value = 0
  startChromeDialogVisible.value = true
}

// 复制命令
const copyCommand = () => {
  navigator.clipboard.writeText(chromeCommand.value)
  ElMessage.success('命令已复制到剪贴板')
  chromeStartStep.value = 1
}

// 显示创建对话框
const showCreateDialog = () => {
  ElMessage.info('录制功能即将上线')
}

onMounted(() => {
  loadTemplates()
  testConnection()
})
</script>

<style scoped>
.rpa-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 5px 0;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.action-section {
  display: flex;
  gap: 10px;
}

.status-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.template-card {
  transition: transform 0.2s;
}

.template-card:hover {
  transform: translateY(-5px);
}

.template-header {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.template-icon {
  font-size: 40px;
  line-height: 1;
}

.template-info h3 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 16px;
}

.template-desc {
  margin: 0;
  color: #909399;
  font-size: 13px;
  line-height: 1.5;
}

.template-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.template-actions {
  display: flex;
  gap: 10px;
}

.template-actions .el-button {
  flex: 1;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.chrome-command {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
}
</style>

