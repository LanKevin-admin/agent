<template>
  <el-container class="app-container">
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <el-icon :size="24"><Monitor /></el-icon>
        <span>RPA监控系统</span>
      </div>
      <el-menu
        :default-active="currentPath"
        router
        class="menu"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#1890ff"
      >
        <el-menu-item index="/">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能对话</span>
        </el-menu-item>
        <el-menu-item index="/voice">
          <el-icon><Microphone /></el-icon>
          <span>语音助手</span>
        </el-menu-item>
        <el-menu-item index="/rpa">
          <el-icon><VideoPlay /></el-icon>
          <span>RPA自动化</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <el-icon><Files /></el-icon>
          <span>分析模板</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><Timer /></el-icon>
          <span>定时任务</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><Search /></el-icon>
          <span>日志分析</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>历史报告</span>
        </el-menu-item>
        <el-menu-item index="/config">
          <el-icon><Setting /></el-icon>
          <span>配置管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="header">
        <span class="title">飞书RPA监控系统</span>
        <span class="subtitle">AI智能日志分析与异常监控</span>
      </el-header>
      
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const currentPath = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.sidebar {
  background-color: #001529;
  height: 100%;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.menu {
  border-right: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 16px;
}

.header .title {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
}

.header .subtitle {
  font-size: 14px;
  color: #8c8c8c;
}

.main-content {
  background-color: #f0f2f5;
  padding: 24px;
}
</style>
