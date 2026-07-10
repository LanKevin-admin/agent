<template>
  <div class="reports">
    <el-card>
      <template #header>
        <div class="header">
          <span>历史报告</span>
          <el-button :icon="Refresh" @click="loadReports" :loading="loading">刷新</el-button>
        </div>
      </template>

      <el-table :data="reports" style="width: 100%;" v-loading="loading">
        <el-table-column prop="filename" label="文件名" min-width="300">
          <template #default="{ row }">
            <el-icon><Document /></el-icon>
            {{ row.filename }}
          </template>
        </el-table-column>
        
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="modified_time" label="修改时间" width="180" />
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="previewReport(row)">
              预览
            </el-button>
            <el-button type="primary" link :icon="Download" @click="downloadReport(row.filename)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && reports.length === 0" description="暂无报告" />
    </el-card>

    <el-dialog v-model="previewVisible" title="报告预览" width="80%" top="5vh">
      <div class="preview-content">
        <pre>{{ previewContent }}</pre>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" :icon="Download" @click="downloadReport(currentFile)">
          下载
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Document, View, Download } from '@element-plus/icons-vue'
import { getReports, getReportDownloadUrl } from '../api'
import axios from 'axios'

const reports = ref([])
const loading = ref(false)
const previewVisible = ref(false)
const previewContent = ref('')
const currentFile = ref('')

const loadReports = async () => {
  loading.value = true
  try {
    const res = await getReports()
    reports.value = res.data.reports || []
  } catch (error) {
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const previewReport = async (row) => {
  try {
    const url = getReportDownloadUrl(row.filename)
    const res = await axios.get(url, { responseType: 'text' })
    previewContent.value = res.data
    currentFile.value = row.filename
    previewVisible.value = true
  } catch (error) {
    ElMessage.error('预览失败')
  }
}

const downloadReport = (filename) => {
  window.open(getReportDownloadUrl(filename), '_blank')
}

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.reports {
  max-width: 1200px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-content {
  max-height: 60vh;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
}

.preview-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.6;
}
</style>
