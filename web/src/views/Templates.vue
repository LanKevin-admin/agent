<template>
  <div class="templates">
    <el-card>
      <template #header>
        <div class="header">
          <span>分析模板管理</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新建模板
          </el-button>
        </div>
      </template>

      <el-alert
        title="什么是分析模板？"
        type="info"
        :closable="false"
        style="margin-bottom: 16px;"
      >
        当你通过智能对话完成一次成功的分析后，可以保存为模板。下次只需说"使用xx模板分析"，AI就会自动复用相同的配置（数据源、SQL查询、字段映射等）
      </el-alert>

      <el-table :data="templates" v-loading="loading" style="width: 100%;">
        <el-table-column prop="name" label="模板名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="data_source" label="数据源" width="120">
          <template #default="{ row }">
            <el-tag :type="row.data_source === 'database' ? 'success' : 'primary'">
              {{ row.data_source === 'database' ? '数据库' : '飞书群' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="viewTemplate(row)">
              查看
            </el-button>
            <el-button type="primary" link :icon="ChatLineRound" @click="useTemplate(row)">
              使用
            </el-button>
            <el-button type="danger" link :icon="Delete" @click="deleteTemplate(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && templates.length === 0" description="暂无模板，通过智能对话创建你的第一个模板吧" />
    </el-card>

    <!-- 查看模板对话框 -->
    <el-dialog v-model="viewDialogVisible" title="模板详情" width="70%">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="模板名称">{{ currentTemplate.name }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ currentTemplate.description }}</el-descriptions-item>
        <el-descriptions-item label="数据源">{{ currentTemplate.data_source }}</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <div class="json-viewer">
        <pre>{{ JSON.stringify(currentTemplate.template, null, 2) }}</pre>
      </div>
    </el-dialog>

    <!-- 创建模板提示对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建分析模板" width="600px">
      <el-alert
        title="推荐通过智能对话创建模板"
        type="success"
        :closable="false"
        style="margin-bottom: 16px;"
      >
        <p>在智能对话中完成一次成功的分析后，对AI说："把这个分析流程保存为模板，名称是xxx"</p>
        <p>AI会自动保存当前的配置（数据源、查询语句、字段映射等）</p>
      </el-alert>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="goToChat">前往智能对话</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Delete, ChatLineRound } from '@element-plus/icons-vue'

const router = useRouter()
const templates = ref([])
const loading = ref(false)
const viewDialogVisible = ref(false)
const showCreateDialog = ref(false)
const currentTemplate = ref({})

// 模拟API调用（实际需要对接后端）
const loadTemplates = async () => {
  loading.value = true
  try {
    // TODO: 调用后端API GET /api/templates
    // const res = await api.get('/api/templates')
    // templates.value = res.data.templates
    
    // 临时模拟数据
    templates.value = []
    ElMessage.info('模板功能需要通过智能对话使用')
  } catch (error) {
    ElMessage.error('获取模板列表失败')
  } finally {
    loading.value = false
  }
}

const viewTemplate = (row) => {
  currentTemplate.value = row
  viewDialogVisible.value = true
}

const useTemplate = (row) => {
  router.push({
    path: '/chat',
    query: { template: row.name }
  })
}

const deleteTemplate = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除模板"${row.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // TODO: 调用后端API DELETE /api/templates/{name}
    ElMessage.success('删除成功')
    loadTemplates()
  } catch {
    // 用户取消
  }
}

const goToChat = () => {
  showCreateDialog.value = false
  router.push('/chat')
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.templates {
  max-width: 1200px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.json-viewer {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.json-viewer pre {
  margin: 0;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.6;
}
</style>
