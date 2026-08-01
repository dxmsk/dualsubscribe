<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close'])

const statusOptions = ['已暂停', '双重订阅', '未识别', '异常']
const statusMeta = {
  已暂停: { icon: 'mdi-pause-circle-outline' },
  双重订阅: { icon: 'mdi-bell-ring-outline' },
  未识别: { icon: 'mdi-help-circle-outline' },
  异常: { icon: 'mdi-alert-circle-outline' },
}

// 设为 true 可脱离后端预览。生产包保持 false，刷新后只读取插件持久化记录。
const USE_MOCK_DATA = false
const MOCK_REMOVED_KEY = 'dualsubscribe_removed_mock_ids'
const mockItems = [
  { id: 1001, title: '肖申克的救赎', category: '类型电影', subscribe_time: '2026-08-01 16:42', release_year: 1994, status: '已暂停', poster: 'https://image.tmdb.org/t/p/w342/9O7gLzmreU0nGkIB6K3BsJbzvNv.jpg', error_log: '' },
  { id: 1002, title: '星际穿越', category: '类型电影', subscribe_time: '2026-08-01 16:31', release_year: 2014, status: '双重订阅', poster: 'https://image.tmdb.org/t/p/w342/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg', error_log: '' },
  { id: 1003, title: '无效的豆瓣条目', category: '类型电影', subscribe_time: '2026-08-01 15:56', release_year: 2026, status: '未识别', poster: '', error_log: '豆瓣 ID 无效，且未能匹配到 TMDB ID' },
  { id: 1004, title: '接口测试电影', category: '类型电影', subscribe_time: '2026-08-01 15:20', release_year: 2025, status: '异常', poster: '', error_log: '目标接口连接超时（10 秒）' },
  { id: 1005, title: '盗梦空间', category: '类型电影', subscribe_time: '2026-08-01 14:48', release_year: 2010, status: '双重订阅', poster: 'https://image.tmdb.org/t/p/w342/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg', error_log: '' },
  { id: 1006, title: '未命名影片', category: '类型电影', subscribe_time: '2026-08-01 14:12', release_year: 0, status: '未识别', poster: '', error_log: '缺少有效 TMDB ID，目标接口仅支持 TMDB ID' },
  { id: 1007, title: '这个杀手不太冷', category: '类型电影', subscribe_time: '2026-08-01 13:45', release_year: 1994, status: '已暂停', poster: 'https://image.tmdb.org/t/p/w342/yI6X2cCM5YPJtxMhUd3dPGqDAhw.jpg', error_log: '' },
  { id: 1008, title: '银翼杀手 2049', category: '类型电影', subscribe_time: '2026-08-01 13:03', release_year: 2017, status: '异常', poster: 'https://image.tmdb.org/t/p/w342/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg', error_log: '目标 MoviePilot 返回 HTTP 401：登录凭据已失效' },
  { id: 1009, title: '楚门的世界', category: '类型电影', subscribe_time: '2026-08-01 12:30', release_year: 1998, status: '双重订阅', poster: '', error_log: '' },
  { id: 1010, title: '千与千寻', category: '类型电影', subscribe_time: '2026-08-01 11:52', release_year: 2001, status: '已暂停', poster: '', error_log: '' },
  { id: 1011, title: '机器人总动员', category: '类型电影', subscribe_time: '2026-08-01 11:08', release_year: 2008, status: '异常', poster: '', error_log: '目标接口返回 500：数据库写入失败' },
  { id: 1012, title: '指环王：护戒使者', category: '类型电影', subscribe_time: '2026-08-01 10:16', release_year: 2001, status: '双重订阅', poster: '', error_log: '' },
]

const items = ref([])
const loading = ref(false)
const error = ref('')
const activeStatus = ref(null)
const multiSelect = ref(false)
const selectedIds = ref([])
const page = ref(1)
const jumpPage = ref(1)
const pageSize = 12

const deleteDialog = ref(false)
const deleting = ref(false)
const pendingDelete = ref(null)
const clearDialog = ref(false)
const clearing = ref(false)
const clearStatus = ref('')
const logDialog = ref(false)
const logItem = ref(null)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('info')

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

function showMessage(text, color = 'info') {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

function mockRemovedIds() {
  try {
    const parsed = JSON.parse(localStorage.getItem(MOCK_REMOVED_KEY) || '[]')
    return Array.isArray(parsed) ? parsed.map(Number) : []
  } catch {
    return []
  }
}

async function loadItems() {
  loading.value = true
  error.value = ''
  try {
    if (USE_MOCK_DATA) {
      const removed = new Set(mockRemovedIds())
      items.value = mockItems.filter(item => !removed.has(Number(item.id)))
    } else {
      const response = await props.api.get('plugin/DualSubscribe/items')
      const data = unwrapResponse(response)
      items.value = Array.isArray(data) ? data : []
    }
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

function statusClass(status) {
  return {
    已暂停: 'badge-paused',
    双重订阅: 'badge-double',
    未识别: 'badge-unknown',
    异常: 'badge-error',
  }[status] || 'badge-unknown'
}

function showStatusLog(item) {
  if (item.status === '已暂停' || item.status === '双重订阅') {
    showMessage('该状态暂无日志记录')
    return
  }
  logItem.value = item
  logDialog.value = true
}

function askDelete(item) {
  pendingDelete.value = item
  deleteDialog.value = true
}

function rememberMockRemoval(id) {
  const removed = new Set(mockRemovedIds())
  removed.add(Number(id))
  localStorage.setItem(MOCK_REMOVED_KEY, JSON.stringify([...removed]))
}

async function unsubscribeItem(item) {
  if (USE_MOCK_DATA) {
    rememberMockRemoval(item.id)
    return { success: true, plugin_success: true, message: '订阅已删除' }
  }
  const response = await props.api.post(`plugin/DualSubscribe/unsubscribe/${item.id}`)
  return unwrapResponse(response) || { success: true, plugin_success: true, message: '订阅已删除' }
}

function removeLocalItem(id) {
  items.value = items.value.filter(value => Number(value.id) !== Number(id))
  selectedIds.value = selectedIds.value.filter(value => Number(value) !== Number(id))
}

async function confirmDelete() {
  const item = pendingDelete.value
  if (!item || deleting.value) return
  deleting.value = true
  try {
    const result = await unsubscribeItem(item)
    removeLocalItem(item.id)
    deleteDialog.value = false
    pendingDelete.value = null
    showMessage(
      result.message || '订阅已删除',
      result.plugin_success === false || result.local_success === false ? 'warning' : 'success',
    )
  } catch (err) {
    showMessage(err?.response?.data?.message || err?.message || '删除请求失败，请稍后重试', 'error')
  } finally {
    deleting.value = false
  }
}

function askClearCurrentStatus() {
  if (!['异常', '未识别'].includes(activeStatus.value)) return
  clearStatus.value = activeStatus.value
  clearDialog.value = true
}

async function confirmClearStatus() {
  if (clearing.value || !['异常', '未识别'].includes(clearStatus.value)) return
  clearing.value = true
  const targets = items.value.filter(item => item.status === clearStatus.value)
  let removed = 0
  let warnings = 0
  let failed = 0
  for (const item of targets) {
    try {
      const result = await unsubscribeItem(item)
      removeLocalItem(item.id)
      removed += 1
      if (result.plugin_success === false || result.local_success === false) warnings += 1
    } catch {
      failed += 1
    }
  }
  clearDialog.value = false
  clearing.value = false
  if (failed) {
    showMessage(`已清除 ${removed} 条，${failed} 条请求失败并保留；${warnings} 条存在取消警告`, 'warning')
  } else if (warnings) {
    showMessage(`已清除 ${removed} 条，其中 ${warnings} 条目标端取消失败但本地记录已移除`, 'warning')
  } else {
    showMessage(`已清除全部 ${removed} 条${clearStatus.value}记录`, 'success')
  }
}

function jump() {
  const target = Math.max(1, Math.min(Number(jumpPage.value) || 1, totalPages.value))
  page.value = target
  jumpPage.value = target
}

watch(activeStatus, () => {
  page.value = 1
  jumpPage.value = 1
})
watch(totalPages, value => {
  if (page.value > value) page.value = value
})
watch(page, value => { jumpPage.value = value })

onMounted(loadItems)
</script>

<template>
  <div class="dual-page">
    <VToolbar density="comfortable" color="transparent" class="px-2">
      <div class="text-h6 font-weight-bold">双重订阅</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" :loading="loading" title="刷新" @click="loadItems" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider />

    <div class="pa-4">
      <VAlert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</VAlert>

      <div class="operation-row mb-4">
        <div class="status-pills">
          <VChip
            v-for="status in statusOptions"
            :key="status"
            variant="flat"
            :prepend-icon="statusMeta[status].icon"
            :class="['status-pill', statusClass(status), { active: activeStatus === status }]"
            @click="toggleStatus(status)"
          >
            {{ status }}({{ counts[status] || 0 }})
          </VChip>
        </div>

        <div class="action-buttons">
          <VBtn
            v-if="['异常', '未识别'].includes(activeStatus) && counts[activeStatus]"
            prepend-icon="mdi-delete-sweep-outline"
            variant="flat"
            :color="activeStatus === '异常' ? 'error' : 'warning'"
            @click="askClearCurrentStatus"
          >
            一键清除{{ activeStatus }}({{ counts[activeStatus] }})
          </VBtn>
          <VMenu>
            <template #activator="{ props: menuProps }">
              <VBtn v-bind="menuProps" prepend-icon="mdi-filter-variant" variant="outlined" color="primary">筛选</VBtn>
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
            <div class="card-layout">
              <div class="poster-frame">
                <VImg
                  v-if="item.poster"
                  :src="item.poster"
                  :alt="item.title"
                  width="76"
                  height="114"
                  contain
                  class="poster-image"
                />
                <VIcon v-else icon="mdi-movie-open-outline" size="34" color="grey" />
              </div>

              <div class="card-body">
                <div class="card-heading">
                  <VCheckboxBtn
                    v-if="multiSelect"
                    :model-value="selectedIds.includes(item.id)"
                    color="primary"
                    class="me-1"
                    @click.stop="toggleSelected(item.id)"
                  />
                  <div class="card-title" :title="item.title">{{ item.title }}</div>
                  <div class="status-controls">
                    <VChip
                      size="small"
                      variant="flat"
                      :class="['status-badge', statusClass(item.status)]"
                      title="查看状态日志"
                      @click.stop="showStatusLog(item)"
                    >
                      {{ item.status }}
                    </VChip>
                    <VBtn
                      icon="mdi-delete-outline"
                      size="x-small"
                      variant="text"
                      color="error"
                      class="delete-button"
                      title="删除订阅"
                      @click.stop="askDelete(item)"
                    />
                  </div>
                </div>
                <div class="meta-line">{{ item.category }} · {{ item.subscribe_time }}</div>
                <div class="meta-line">发行年份：{{ item.release_year || '-' }}</div>
              </div>
            </div>
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

    <VDialog v-model="deleteDialog" max-width="480" persistent>
      <VCard>
        <VCardTitle class="d-flex align-center ga-2">
          <VIcon icon="mdi-alert-outline" color="warning" />
          删除订阅
        </VCardTitle>
        <VCardText>
          确认删除《{{ pendingDelete?.title }}》的订阅吗？这将同时取消插件中的订阅。
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" :disabled="deleting" @click="deleteDialog = false">取消</VBtn>
          <VBtn color="error" variant="flat" :loading="deleting" @click="confirmDelete">确认删除</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VDialog v-model="clearDialog" max-width="500" persistent>
      <VCard>
        <VCardTitle class="d-flex align-center ga-2">
          <VIcon icon="mdi-delete-sweep-outline" :color="clearStatus === '异常' ? 'error' : 'warning'" />
          一键清除{{ clearStatus }}
        </VCardTitle>
        <VCardText>
          确认清除全部 {{ counts[clearStatus] || 0 }} 条“{{ clearStatus }}”记录吗？
          这将同时取消对应的 MP 订阅和已创建的目标端订阅，操作无法撤销。
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" :disabled="clearing" @click="clearDialog = false">取消</VBtn>
          <VBtn
            :color="clearStatus === '异常' ? 'error' : 'warning'"
            variant="flat"
            :loading="clearing"
            @click="confirmClearStatus"
          >
            确认清除
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VDialog v-model="logDialog" max-width="560">
      <VCard>
        <VCardTitle class="d-flex align-center ga-2">
          <VIcon icon="mdi-text-box-search-outline" color="primary" />
          状态日志
        </VCardTitle>
        <VCardSubtitle v-if="logItem">《{{ logItem.title }}》</VCardSubtitle>
        <VCardText class="log-content">{{ logItem?.error_log || '暂无详细错误日志' }}</VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn color="primary" variant="tonal" @click="logDialog = false">关闭</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VSnackbar v-model="snackbar" :color="snackbarColor" timeout="4500" location="bottom">
      {{ snackbarText }}
      <template #actions>
        <VBtn variant="text" @click="snackbar = false">关闭</VBtn>
      </template>
    </VSnackbar>
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
  font-weight: 700;
  opacity: 0.76;
  transition: opacity 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.status-pill:hover,
.status-pill.active {
  opacity: 1;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.18);
}

.subscription-card {
  min-height: 140px;
  padding: 12px;
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

.card-layout {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.poster-frame {
  width: 78px;
  height: 116px;
  flex: 0 0 78px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.poster-image {
  width: 76px;
  height: 114px;
}

.card-body {
  min-width: 0;
  flex: 1;
}

.card-heading {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.card-title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-top: 3px;
  font-size: 1.05rem;
  font-weight: 700;
}

.status-controls {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.status-badge {
  cursor: pointer;
  flex-shrink: 0;
  font-weight: 700;
}

.delete-button {
  margin-right: -4px;
}

.badge-paused {
  color: #3f3f46 !important;
  background: linear-gradient(135deg, #a1a1aa, #f59e0b) !important;
}

.badge-double {
  color: #fff !important;
  background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
}

.badge-unknown {
  color: #422006 !important;
  background: #facc15 !important;
}

.badge-error {
  color: #fff !important;
  background: #ef4444 !important;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.18);
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

.log-content {
  margin-top: 12px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.7;
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
