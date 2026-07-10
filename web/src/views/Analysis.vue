<template>
  <div class="analysis">
    <el-card>
      <template #header>
        <span>RPA日志分析</span>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="时间范围">
          <el-row :gutter="8">
            <el-col :span="11">
              <el-time-select
                v-model="form.start_time"
                placeholder="开始时间"
                start="00:00"
                step="00:30"
                end="23:30"
              />
            </el-col>
            <el-col :span="2" style="text-align: center;">至</el-col>
            <el-col :span="11">
              <el-time-select
                v-model="form.end_time"
                placeholder="结束时间"
                start="00:00"
                step="00:30"
                end="23:59"
              />
            </el-col>
          </el-row>
          <div class="hint">留空表示全天，例如：14:00至23:59表示下午2点后的日志</div>
        </el-form-item>

        <el-form-item label="自定义查询">
          <el-input
            v-model="form.query"
            type="textarea"
            :rows="3"
            placeholder="可选：用自然语言描述需要分析的内容，例如：分析今天的RPA日志，生成领导汇报"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="startAnalysis" :loading="analyzing" :icon="Search">
            开始分析
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" style="margin-top: 16px;">
      <template #header>
        <span>分析结果</span>
      </template>
      
      <el-alert
        v-if="result.status === 'success'"
        title="分析完成"
        type="success"
        :closable="false"
        style="margin-bottom: 16px;"
      />
      
      <el-alert
        v-else-if="result.status === 'error'"
        title="分析失败"
        type="error"
        :closable="false"
        style="margin-bottom: 16px;"
      >
        {{ result.error }}
      </el-alert>

      <div v-if="result.summary" class="summary-section">
        <el-divider content-position="left">执行摘要</el-divider>
        <pre class="summary-text">{{ result.summary }}</pre>
      </div>

      <div v-if="result.report_file" class="report-section">
        <el-divider content-position="left">生成的报告</el-divider>
        <el-tag type="success" size="large">
          <el-icon><Document /></el-icon>
          {{ result.report_file }}
        </el-tag>
        <el-button
          type="primary"
          link
          :icon="Download"
          @click="downloadReport(result.report_file)"
          style="margin-left: 12px;"
        >
          下载报告
        </el-button>
      </div>

      <div v-if="result.details && result.details.length > 0" class="details-section">
        <el-divider content-position="left">详细日志</el-divider>
        <el-timeline>
          <el-timeline-item
            v-for="(item, index) in result.details"
            :key="index"
            :timestamp="item.time"
            placement="top"
          >
            <el-card>
              <p><strong>{{ item.action }}</strong></p>
              <p v-if="item.result">{{ item.result }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document, Download } from '@element-plus/icons-vue'
import { analyzeLog, getReportDownloadUrl } from '../api'

const dateRange = ref([])
const form = ref({
  start_date: '',
  end_date: '',
  start_time: '',
  end_time: '',
  query: ''
})
const analyzing = ref(false)
const result = ref(null)

watch(dateRange, (val) => {
  if (val && val.length === 2) {
    form.value.start_date = val[0]
    form.value.end_date = val[1]
  } else {
    form.value.start_date = ''
    form.value.end_date = ''
  }
})

const startAnalysis = async () => {
  if (!form.value.start_date || !form.value.end_date) {
    ElMessage.warning('请选择日期范围')
    return
  }

  analyzing.value = true
  result.value = null

  try {
    const res = await analyzeLog(form.value)
    result.value = res.data
    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error('分析失败: ' + (error.response?.data?.detail || error.message))
    result.value = { status: 'error', error: error.response?.data?.detail || error.message }
  } finally {
    analyzing.value = false
  }
}

const resetForm = () => {
  dateRange.value = []
  form.value = {
    start_date: '',
    end_date: '',
    start_time: '',
    end_time: '',
    query: ''
  }
  result.value = null
}

const downloadReport = (filename) => {
  window.open(getReportDownloadUrl(filename), '_blank')
}
</script>

<style scoped>
.analysis {
  max-width: 1000px;
}

.hint {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.summary-section,
.report-section,
.details-section {
  margin-top: 16px;
}

.summary-text {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.6;
}
</style>
