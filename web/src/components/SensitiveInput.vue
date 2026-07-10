<template>
  <div class="sensitive-field">
    <el-input
      v-model="displayValue"
      :type="isVisible ? 'text' : 'password'"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="handleInput"
    >
      <template #suffix>
        <el-icon @click="toggleVisibility" style="cursor: pointer;">
          <View v-if="!isVisible" />
          <Hide v-if="isVisible" />
        </el-icon>
      </template>
    </el-input>
    <div v-if="isMasked" class="mask-hint">
      <el-icon><InfoFilled /></el-icon>
      <span>敏感信息已脱敏，修改时请输入完整内容</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { View, Hide, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isVisible = ref(false)
const displayValue = ref(props.modelValue)

// 检查是否是脱敏数据（包含****)
const isMasked = computed(() => {
  return displayValue.value && displayValue.value.includes('****')
})

watch(() => props.modelValue, (newVal) => {
  displayValue.value = newVal
})

const toggleVisibility = () => {
  isVisible.value = !isVisible.value
}

const handleInput = (value) => {
  // 如果输入了新值（不是脱敏数据），才更新
  if (!value.includes('****')) {
    emit('update:modelValue', value)
  }
}
</script>

<style scoped>
.sensitive-field {
  width: 100%;
}

.mask-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: #faad14;
}

.mask-hint .el-icon {
  font-size: 14px;
}
</style>
