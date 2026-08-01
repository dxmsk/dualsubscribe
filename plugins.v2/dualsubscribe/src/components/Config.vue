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
  primary_enabled: true,
  endpoint: '',
  timeout: 10,
  pause_minutes: 30,
  username: 'admin',
  password: 'admin',
  sync_before_auto_search: false,
  headers: '',
  secondary_enabled: false,
  secondary_endpoint: 'http://192.168.1.6:3300/api/v1/subscription/create',
  secondary_token: '',
  secondary_account_id: 'b9767d9d-466a-4af9-b984-282bab6cf81b',
  secondary_target_directory: '/待整理',
  secondary_quality_preference: '1080p',
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
        :disabled="!config.primary_enabled"
      />
      <VSwitch
        v-model="config.primary_enabled"
        label="同步兼容 MoviePilot 目标"
        color="primary"
        hint="29999 代理不返回订阅 ID 时，可关闭此项并只使用下方附加接口"
        persistent-hint
      />
      <VTextarea
        v-model="config.headers"
        label="额外请求头（JSON，可选）"
        rows="3"
        placeholder='{"Authorization": "Bearer ..."}'
        :disabled="!config.primary_enabled"
      />
      <VSwitch
        v-model="config.sync_before_auto_search"
        label="MoviePilot 自动搜索前再次同步目标端"
        color="primary"
      />

      <VDivider class="my-5" />
      <div class="text-subtitle-1 font-weight-bold mb-3">附加订阅接口（3300）</div>
      <VSwitch
        v-model="config.secondary_enabled"
        label="同时提交到附加订阅接口"
        color="primary"
        hint="开启后新增订阅会同时调用 /api/v1/subscription/create"
        persistent-hint
      />
      <VTextField
        v-model="config.secondary_endpoint"
        label="附加接口新增 URL"
        placeholder="http://host:3300/api/v1/subscription/create"
        :disabled="!config.secondary_enabled"
      />
      <VTextField
        v-model="config.secondary_token"
        label="附加接口 Bearer Token"
        type="password"
        autocomplete="off"
        hint="只填写 Token 内容，不要包含 Bearer 前缀"
        persistent-hint
        :disabled="!config.secondary_enabled"
      />
      <VRow>
        <VCol cols="12" md="6">
          <VTextField
            v-model="config.secondary_account_id"
            label="附加接口账号 ID"
            :disabled="!config.secondary_enabled"
          />
        </VCol>
        <VCol cols="12" md="6">
          <VTextField
            v-model="config.secondary_target_directory"
            label="目标目录"
            placeholder="/待整理"
            :disabled="!config.secondary_enabled"
          />
        </VCol>
      </VRow>
      <VTextField
        v-model="config.secondary_quality_preference"
        label="画质偏好"
        placeholder="1080p"
        :disabled="!config.secondary_enabled"
      />
      <VAlert type="info" variant="tonal" class="mt-3">
        兼容 MP 目标和附加接口都会立即订阅；删除卡片时会按各自保存或回查到的 ID 联动取消。Token 不会写入插件日志。
      </VAlert>
    </VContainer>
  </div>
</template>
