<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['close'])
const statusOptions = ['已暂停', '双重订阅', '未识别', '异常']
const statusMeta = {
  已暂停: { color: 'orange-darken-1', icon: 'mdi-pause-circle-outline' },
  双重订阅: { color: 'deep-purple-accent-2', icon: 'mdi-bell-ring-outline' },
  未识别: { color: 'amber-darken-2', icon: 'mdi-help-circle-outline' },
  异常: { color: 'red-accent-3', icon: 'mdi-alert-circle-outline' },
}

const items = ref([])
const loading = ref(false)
const error = ref('')
const activeStatus = ref(null)
const multiSelect = ref(false)
const selectedIds = ref([])
const page = ref(1)
const jumpPage = ref(1)
const pageSize = 12

const counts = computed(() => Object.fromEntries(
  statusOptions.map(status => [status, items.value.filter(item => item.status === status).length]),
))
const filteredItems = computed(() => activeStatus.value
  ? items.value.filter(item => item.status === activeStatus.value)
  : items.value)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / pageSize)))
const visibleItems = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredItems.value.slice(start, start + pageSize)
})

function unwrapResponse(response) {
  return response?.data?.data ?? response?.data ?? response ?? []
}

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    const response = await props.api.get('plugin/DualSubscribe/items')
    const data = unwrapResponse(response)
    items.value = Array.isArray(data) ? data : []
  } catch (err) {
    error.value = err?.message || '订阅数据加载失败'
  } finally {
    loading.value = false
  }
}

function toggleStatus(status) {
  activeStatus.value = activeStatus.value === status ? null : status
}

function toggleMultiSelect() {
  multiSelect.value = !multiSelect.value
  if (!multiSelect.value) selectedIds.value = []
}

function toggleSelected(id) {
  if (!multiSelect.value) return
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter(value => value !== id)
    : [...selectedIds.value, id]
}

function jump() {
  const target = Math.max(1, Math.min(Number(jumpPage.value) || 1, totalPages.value))
  page.value = target
  jumpPage.value = target
}

watch([activeStatus, () => items.value.length], () => {
  page.value = 1
  jumpPage.value = 1
})
watch(page, value => { jumpPage.value = value })

onMounted(loadItems)
</script>

<template>
  <div class="dual-page">
    <VToolbar density="comfortable" color="transparent" class="px-2">
      <div class="text-h6 font-weight-bold">双重订阅</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" :loading="loading" @click="loadItems" />
      <VBtn icon="mdi-close" variant="text" @click="emit('close')" />
    </VToolbar>
    <VDivider />

    <div class="pa-4">
      <VAlert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</VAlert>

      <div class="operation-row mb-4">
        <div class="status-pills">
          <VChip
            v-for="status in statusOptions"
            :key="status"
            :color="statusMeta[status].color"
            :variant="activeStatus === status ? 'flat' : 'tonal'"
            :prepend-icon="statusMeta[status].icon"
            class="status-pill"
            @click="toggleStatus(status)"
          >
            {{ status }}({{ counts[status] || 0 }})
          </VChip>
        </div>

        <div class="action-buttons">
          <VMenu>
            <template #activator="{ props: menuProps }">
              <VBtn v-bind="menuProps" prepend-icon="mdi-filter-variant" variant="outlined" color="primary">
                筛选
              </VBtn>
            </template>
            <VList density="compact">
              <VListItem title="全部状态" @click="activeStatus = null" />
              <VListItem
                v-for="status in statusOptions"
                :key="status"
                :title="`${status}(${counts[status] || 0})`"
                @click="activeStatus = status"
              />
            </VList>
          </VMenu>
          <VBtn
            prepend-icon="mdi-checkbox-multiple-marked-outline"
            :variant="multiSelect ? 'flat' : 'tonal'"
            color="primary"
            @click="toggleMultiSelect"
          >
            {{ multiSelect ? `完成(${selectedIds.length})` : '多选' }}
          </VBtn>
        </div>
      </div>

      <VProgressLinear v-if="loading" indeterminate color="primary" class="mb-3" />
      <VRow v-if="visibleItems.length" dense>
        <VCol v-for="item in visibleItems" :key="item.id" cols="12" sm="6" md="4" lg="3">
          <VCard
            class="subscription-card"
            :class="{ selected: selectedIds.includes(item.id) }"
            variant="flat"
            @click="toggleSelected(item.id)"
          >
            <div class="card-heading">
              <VCheckboxBtn
                v-if="multiSelect"
                :model-value="selectedIds.includes(item.id)"
                color="primary"
                class="me-1"
                @click.stop="toggleSelected(item.id)"
              />
              <div class="card-title" :title="item.title">{{ item.title }}</div>
              <VChip
                :color="statusMeta[item.status]?.color || 'grey'"
                size="small"
                variant="flat"
                class="status-badge"
              >
                {{ item.status }}
              </VChip>
            </div>
            <div class="meta-line">{{ item.category }} · {{ item.subscribe_time }}</div>
            <div class="meta-line">发行年份：{{ item.release_year || '-' }}</div>
          </VCard>
        </VCol>
      </VRow>
      <VAlert v-else-if="!loading" type="info" variant="tonal">当前筛选条件下暂无订阅</VAlert>

      <div class="pagination-row mt-5">
        <VPagination v-model="page" :length="totalPages" :total-visible="5" density="comfortable" />
        <VTextField
          v-model.number="jumpPage"
          type="number"
          min="1"
          :max="totalPages"
          density="compact"
          variant="outlined"
          hide-details
          class="jump-input"
          @keyup.enter="jump"
        />
        <VBtn color="primary" variant="tonal" @click="jump">跳转</VBtn>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dual-page {
  min-height: 540px;
  background: rgb(var(--v-theme-background));
}

.operation-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.status-pills,
.action-buttons,
.pagination-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.status-pill {
  cursor: pointer;
  font-weight: 600;
}

.subscription-card {
  min-height: 118px;
  padding: 16px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  transition: border-color 0.18s ease, transform 0.18s ease;
}

.subscription-card:hover {
  border-color: rgb(var(--v-theme-primary));
  transform: translateY(-1px);
}

.subscription-card.selected {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 1px rgb(var(--v-theme-primary));
}

.card-heading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.card-title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1.05rem;
  font-weight: 700;
}

.status-badge {
  flex-shrink: 0;
  font-weight: 700;
}

.meta-line {
  color: rgba(var(--v-theme-on-surface), 0.62);
  font-size: 0.84rem;
  line-height: 1.75;
}

.pagination-row {
  justify-content: center;
}

.jump-input {
  flex: 0 0 86px;
  max-width: 86px;
}

@media (max-width: 600px) {
  .action-buttons,
  .status-pills {
    width: 100%;
  }

  .action-buttons {
    justify-content: flex-end;
  }
}
</style>
