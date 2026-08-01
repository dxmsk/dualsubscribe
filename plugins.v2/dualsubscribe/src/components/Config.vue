<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['save', 'close'])

const config = ref({
  enabled: false,
  endpoint: '',
  timeout: 10,
  pause_minutes: 30,
  username: 'admin',
  password: 'admin',
  sync_before_auto_search: false,
  headers: '',
})

function saveConfig() {
  const payload = {
    ...config.value,
    timeout: Math.max(1, Math.min(Number(config.value.timeout) || 10, 60)),
    pause_minutes: Math.max(1, Math.min(Number(config.value.pause_minutes) || 30, 10080)),
  }
  emit('save', payload)
}

onMounted(() => {
  config.value = {
    ...config.value,
    ...(props.initialConfig || {}),
  }
})
</script>

<template>
  <div class="dual-config">
    <VToolbar density="comfortable" color="transparent">
      <div class="text-h6 ms-3">双重订阅配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" color="primary" variant="text" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" @click="emit('close')" />
    </VToolbar>
    <VDivider />

    <VContainer class="pt-5">
      <VRow>
        <VCol cols="12" md="4">
          <VSwitch v-model="config.enabled" label="启用插件" color="primary" />
        </VCol>
        <VCol cols="12" md="4">
          <VTextField
            v-model.number="config.pause_minutes"
            type="number"
            min="1"
            max="10080"
            label="本地暂停时间（分钟）"
            hint="仅影响保存后新增的订阅"
            persistent-hint
          />
        </VCol>
        <VCol cols="12" md="4">
          <VTextField
            v-model.number="config.timeout"
            type="number"
            min="1"
            max="60"
            label="接口超时（秒）"
          />
        </VCol>
      </VRow>

      <VRow>
        <VCol cols="12" md="6">
          <VTextField v-model="config.username" label="目标 MoviePilot 用户名" autocomplete="username" />
        </VCol>
        <VCol cols="12" md="6">
          <VTextField
            v-model="config.password"
            label="目标 MoviePilot 密码"
            type="password"
            autocomplete="current-password"
          />
        </VCol>
      </VRow>

      <VTextField
        v-model="config.endpoint"
        label="外部 MoviePilot 兼容订阅接口"
        placeholder="http://host/path/api/v1/subscribe/"
      />
      <VTextarea
        v-model="config.headers"
        label="额外请求头（JSON，可选）"
        rows="3"
        placeholder='{"Authorization": "Bearer ..."}'
      />
      <VSwitch
        v-model="config.sync_before_auto_search"
        label="MoviePilot 自动搜索前再次同步目标端"
        color="primary"
      />
      <VAlert type="info" variant="tonal" class="mt-3">
        目标端立即订阅；MoviePilot 本地暂停设定分钟数。恢复前如果 Emby 已完整入库，插件会直接取消本地暂停订阅。
      </VAlert>
    </VContainer>
  </div>
</template>
