import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API请求失败:', error)
    return Promise.reject(error)
  }
)

// 健康检查
export const getHealth = () => api.get('/health')

// 获取配置（脱敏）
export const getConfig = () => api.get('/config')

// 保存配置
export const saveConfig = (data) => api.post('/config', data)

// 分析日志
export const analyzeLog = (data) => api.post('/analyze', data)

// 获取报告列表
export const getReports = () => api.get('/reports')

// 下载报告文件URL
export const getReportDownloadUrl = (filename) => `/api/reports/${filename}`

// ==================== 对话历史 ====================

// 获取所有会话列表
export const getSessions = () => api.get('/conversations/sessions')

// 获取指定会话的对话历史
export const getSessionHistory = (sessionId) => api.get(`/conversations/${sessionId}`)

// 清空指定会话的历史记录
export const clearSession = (sessionId) => api.delete(`/conversations/${sessionId}`)

// ==================== 定时任务 ====================

// 获取所有任务
export const getTasks = (enabledOnly = false) => api.get('/tasks', { params: { enabled_only: enabledOnly } })

// 创建任务
export const createTask = (data) => api.post('/tasks', data)

// 获取任务详情
export const getTask = (taskId) => api.get(`/tasks/${taskId}`)

// 更新任务
export const updateTask = (taskId, data) => api.put(`/tasks/${taskId}`, data)

// 删除任务
export const deleteTask = (taskId) => api.delete(`/tasks/${taskId}`)

// 获取任务执行历史
export const getTaskExecutions = (taskId, limit = 50) => api.get(`/tasks/${taskId}/executions`, { params: { limit } })

