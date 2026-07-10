<template>
  <div class="tasks-page">
    <el-card>
      <template #header>
        <div class="header">
          <span>定时任务管理</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog">新建任务</el-button>
        </div>
      </template>

      <el-table :data="tasks" stripe v-loading="loading">
        <el-table-column prop="task_name" label="任务名称" width="200" />
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="{ row }">
            <el-tag :type="taskTypeColor(row.task_type)">{{ row.task_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="cron_expression" label="Cron表达式" width="150" />
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="toggleTask(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次运行" width="180">
          <template #default="{ row }">
            {{ row.last_run_at ? formatTime(row.last_run_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="next_run_at" label="下次运行" width="180">
          <template #default="{ row }">
            {{ row.next_run_at ? formatTime(row.next_run_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="viewExecutions(row)">执行历史</el-button>
            <el-button type="primary" link :icon="Edit" @click="editTask(row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" @click="deleteTask(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="taskForm" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.task_name" placeholder="例如：每日日志汇报" />
        </el-form-item>
        <el-form-item label="任务类型" required>
          <el-select v-model="taskForm.task_type" placeholder="选择任务类型">
            <el-option label="日志分析" value="analyze" />
            <el-option label="生成报告" value="report" />
            <el-option label="数据同步" value="sync" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" placeholder="简要描述任务内容" />
        </el-form-item>
        <el-form-item label="Cron表达式" required>
          <el-input v-model="taskForm.cron_expression" placeholder="例如：0 18 * * * (每天18:00)" />
          <div class="cron-hint">
            <p>常用示例：</p>
            <ul>
              <li>0 18 * * * - 每天18:00</li>
              <li>0 9,18 * * * - 每天9:00和18:00</li>
              <li>0 18 * * 1-5 - 每周一到周五18:00</li>
            </ul>
          </div>
        </el-form-item>
        <el-form-item label="执行指令">
          <el-input v-model="taskForm.query_text" type="textarea" :rows="3" 
                    placeholder="例如：分析今天的RPA日志并生成报告发送给业务负责人" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="taskForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTask" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行历史对话框 -->
    <el-dialog v-model="executionsVisible" title="执行历史" width="800px">
      <el-table :data="executions" stripe v-loading="executionsLoading" max-height="400">
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusColor(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration ? row.duration.toFixed(2) + 's' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, View } from '@element-plus/icons-vue'
import { getTasks, createTask, updateTask, deleteTask as deleteTaskApi, getTaskExecutions } from '../api'

const tasks = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新建任务')
const saving = ref(false)
const isEdit = ref(false)
const editingTaskId = ref(null)

const taskForm = ref({
  task_name: '',
  task_type: 'analyze',
  description: '',
  cron_expression: '',
  query_text: '',
  enabled: true
})

const executions = ref([])
const executionsVisible = ref(false)
const executionsLoading = ref(false)

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const res = await getTasks()
    if (res.data.success) {
      tasks.value = res.data.tasks
    }
  } catch (error) {
    ElMessage.error('加载任务列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  dialogTitle.value = '新建任务'
  taskForm.value = {
    task_name: '',
    task_type: 'analyze',
    description: '',
    cron_expression: '',
    query_text: '',
    enabled: true
  }
  dialogVisible.value = true
}

// 编辑任务
const editTask = (task) => {
  isEdit.value = true
  editingTaskId.value = task.id
  dialogTitle.value = '编辑任务'
  taskForm.value = {
    task_name: task.task_name,
    task_type: task.task_type,
    description: task.description,
    cron_expression: task.cron_expression,
    query_text: task.query_text,
    enabled: task.enabled
  }
  dialogVisible.value = true
}

// 保存任务
const saveTask = async () => {
  if (!taskForm.value.task_name || !taskForm.value.task_type || !taskForm.value.cron_expression) {
    ElMessage.warning('请填写必填项')
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await updateTask(editingTaskId.value, taskForm.value)
      ElMessage.success('任务已更新')
    } else {
      await createTask(taskForm.value)
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
    loadTasks()
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  } finally {
    saving.value = false
  }
}

// 切换任务启用状态
const toggleTask = async (task) => {
  try {
    await updateTask(task.id, { ...task, enabled: task.enabled })
    ElMessage.success(task.enabled ? '任务已启用' : '任务已禁用')
  } catch (error) {
    ElMessage.error('更新失败：' + error.message)
    task.enabled = !task.enabled // 恢复原状态
  }
}

// 删除任务
const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务"${task.task_name}"吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteTaskApi(task.id)
    ElMessage.success('任务已删除')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

// 查看执行历史
const viewExecutions = async (task) => {
  executionsVisible.value = true
  executionsLoading.value = true
  try {
    const res = await getTaskExecutions(task.id)
    if (res.data.success) {
      executions.value = res.data.executions
    }
  } catch (error) {
    ElMessage.error('加载执行历史失败：' + error.message)
  } finally {
    executionsLoading.value = false
  }
}

// 工具函数
const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const taskTypeColor = (type) => {
  const colors = {
    'analyze': 'primary',
    'report': 'success',
    'sync': 'info',
    'custom': 'warning'
  }
  return colors[type] || 'info'
}

const statusColor = (status) => {
  const colors = {
    'running': 'info',
    'success': 'success',
    'failed': 'danger'
  }
  return colors[status] || 'info'
}

const statusText = (status) => {
  const texts = {
    'running': '运行中',
    'success': '成功',
    'failed': '失败'
  }
  return texts[status] || status
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.tasks-page {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cron-hint {
  margin-top: 8px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.cron-hint p {
  margin: 0 0 8px;
  font-weight: bold;
}

.cron-hint ul {
  margin: 0;
  padding-left: 20px;
}

.cron-hint li {
  margin: 4px 0;
}
</style>


