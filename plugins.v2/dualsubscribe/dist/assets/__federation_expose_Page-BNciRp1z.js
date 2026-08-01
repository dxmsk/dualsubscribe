import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass,mergeProps:_mergeProps,withModifiers:_withModifiers,withKeys:_withKeys} = await importShared('vue');


const _hoisted_1 = { class: "dual-page" };
const _hoisted_2 = { class: "pa-4" };
const _hoisted_3 = { class: "operation-row mb-4" };
const _hoisted_4 = { class: "status-pills" };
const _hoisted_5 = { class: "action-buttons" };
const _hoisted_6 = { class: "card-layout" };
const _hoisted_7 = { class: "poster-frame" };
const _hoisted_8 = { class: "card-body" };
const _hoisted_9 = { class: "card-heading" };
const _hoisted_10 = ["title"];
const _hoisted_11 = { class: "status-controls" };
const _hoisted_12 = { class: "meta-line" };
const _hoisted_13 = { class: "meta-line" };
const _hoisted_14 = { class: "pagination-row mt-5" };

const {computed,onMounted,ref,watch} = await importShared('vue');


const USE_MOCK_DATA = false;
const MOCK_REMOVED_KEY = 'dualsubscribe_removed_mock_ids';
const pageSize = 12;


const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const statusOptions = ['已暂停', '双重订阅', '未识别', '异常'];
const statusMeta = {
  已暂停: { icon: 'mdi-pause-circle-outline' },
  双重订阅: { icon: 'mdi-bell-ring-outline' },
  未识别: { icon: 'mdi-help-circle-outline' },
  异常: { icon: 'mdi-alert-circle-outline' },
};

// 设为 true 可脱离后端预览。生产包保持 false，刷新后只读取插件持久化记录。
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
];

const items = ref([]);
const loading = ref(false);
const error = ref('');
const activeStatus = ref(null);
const multiSelect = ref(false);
const selectedIds = ref([]);
const page = ref(1);
const jumpPage = ref(1);
const deleteDialog = ref(false);
const deleting = ref(false);
const pendingDelete = ref(null);
const logDialog = ref(false);
const logItem = ref(null);
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('info');

const counts = computed(() => Object.fromEntries(
  statusOptions.map(status => [status, items.value.filter(item => item.status === status).length]),
));
const filteredItems = computed(() => activeStatus.value
  ? items.value.filter(item => item.status === activeStatus.value)
  : items.value);
const totalPages = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / pageSize)));
const visibleItems = computed(() => {
  const start = (page.value - 1) * pageSize;
  return filteredItems.value.slice(start, start + pageSize)
});

function unwrapResponse(response) {
  return response?.data?.data ?? response?.data ?? response ?? []
}

function showMessage(text, color = 'info') {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
}

function mockRemovedIds() {
  try {
    const parsed = JSON.parse(localStorage.getItem(MOCK_REMOVED_KEY) || '[]');
    return Array.isArray(parsed) ? parsed.map(Number) : []
  } catch {
    return []
  }
}

async function loadItems() {
  loading.value = true;
  error.value = '';
  try {
    if (USE_MOCK_DATA) ; else {
      const response = await props.api.get('plugin/DualSubscribe/items');
      const data = unwrapResponse(response);
      items.value = Array.isArray(data) ? data : [];
    }
  } catch (err) {
    error.value = err?.message || '订阅数据加载失败';
  } finally {
    loading.value = false;
  }
}

function toggleStatus(status) {
  activeStatus.value = activeStatus.value === status ? null : status;
}

function toggleMultiSelect() {
  multiSelect.value = !multiSelect.value;
  if (!multiSelect.value) selectedIds.value = [];
}

function toggleSelected(id) {
  if (!multiSelect.value) return
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter(value => value !== id)
    : [...selectedIds.value, id];
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
    showMessage('该状态暂无日志记录');
    return
  }
  logItem.value = item;
  logDialog.value = true;
}

function askDelete(item) {
  pendingDelete.value = item;
  deleteDialog.value = true;
}

async function confirmDelete() {
  const item = pendingDelete.value;
  if (!item || deleting.value) return
  deleting.value = true;
  try {
    let result = { success: true, plugin_success: true, message: '订阅已删除' };
    if (USE_MOCK_DATA) ; else {
      const response = await props.api.post(`plugin/DualSubscribe/unsubscribe/${item.id}`);
      result = unwrapResponse(response) || result;
    }

    items.value = items.value.filter(value => Number(value.id) !== Number(item.id));
    selectedIds.value = selectedIds.value.filter(value => Number(value) !== Number(item.id));
    deleteDialog.value = false;
    pendingDelete.value = null;
    showMessage(
      result.message || '订阅已删除',
      result.plugin_success === false || result.local_success === false ? 'warning' : 'success',
    );
  } catch (err) {
    showMessage(err?.response?.data?.message || err?.message || '删除请求失败，请稍后重试', 'error');
  } finally {
    deleting.value = false;
  }
}

function jump() {
  const target = Math.max(1, Math.min(Number(jumpPage.value) || 1, totalPages.value));
  page.value = target;
  jumpPage.value = target;
}

watch(activeStatus, () => {
  page.value = 1;
  jumpPage.value = 1;
});
watch(totalPages, value => {
  if (page.value > value) page.value = value;
});
watch(page, value => { jumpPage.value = value; });

onMounted(loadItems);

return (_ctx, _cache) => {
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VChip = _resolveComponent("VChip");
  const _component_VListItem = _resolveComponent("VListItem");
  const _component_VList = _resolveComponent("VList");
  const _component_VMenu = _resolveComponent("VMenu");
  const _component_VProgressLinear = _resolveComponent("VProgressLinear");
  const _component_VImg = _resolveComponent("VImg");
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VCheckboxBtn = _resolveComponent("VCheckboxBtn");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VPagination = _resolveComponent("VPagination");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCardActions = _resolveComponent("VCardActions");
  const _component_VDialog = _resolveComponent("VDialog");
  const _component_VCardSubtitle = _resolveComponent("VCardSubtitle");
  const _component_VSnackbar = _resolveComponent("VSnackbar");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-2"
    }, {
      default: _withCtx(() => [
        _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-h6 font-weight-bold" }, "双重订阅", -1 /* CACHED */)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          icon: "mdi-refresh",
          variant: "text",
          loading: loading.value,
          title: "刷新",
          onClick: loadItems
        }, null, 8 /* PROPS */, ["loading"]),
        _createVNode(_component_VBtn, {
          icon: "mdi-close",
          variant: "text",
          title: "关闭",
          onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
        })
      ]),
      _: 1 /* STABLE */
    }),
    _createVNode(_component_VDivider),
    _createElementVNode("div", _hoisted_2, [
      (error.value)
        ? (_openBlock(), _createBlock(_component_VAlert, {
            key: 0,
            type: "error",
            variant: "tonal",
            class: "mb-4"
          }, {
            default: _withCtx(() => [
              _createTextVNode(_toDisplayString(error.value), 1 /* TEXT */)
            ]),
            _: 1 /* STABLE */
          }))
        : _createCommentVNode("v-if", true),
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          (_openBlock(), _createElementBlock(_Fragment, null, _renderList(statusOptions, (status) => {
            return _createVNode(_component_VChip, {
              key: status,
              variant: "flat",
              "prepend-icon": statusMeta[status].icon,
              class: _normalizeClass(['status-pill', statusClass(status), { active: activeStatus.value === status }]),
              onClick: $event => (toggleStatus(status))
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(status) + "(" + _toDisplayString(counts.value[status] || 0) + ") ", 1 /* TEXT */)
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["prepend-icon", "class", "onClick"])
          }), 64 /* STABLE_FRAGMENT */))
        ]),
        _createElementVNode("div", _hoisted_5, [
          _createVNode(_component_VMenu, null, {
            activator: _withCtx(({ props: menuProps }) => [
              _createVNode(_component_VBtn, _mergeProps(menuProps, {
                "prepend-icon": "mdi-filter-variant",
                variant: "outlined",
                color: "primary"
              }), {
                default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                  _createTextVNode("筛选", -1 /* CACHED */)
                ]))]),
                _: 1 /* STABLE */
              }, 16 /* FULL_PROPS */)
            ]),
            default: _withCtx(() => [
              _createVNode(_component_VList, { density: "compact" }, {
                default: _withCtx(() => [
                  _createVNode(_component_VListItem, {
                    title: "全部状态",
                    onClick: _cache[1] || (_cache[1] = $event => (activeStatus.value = null))
                  }),
                  (_openBlock(), _createElementBlock(_Fragment, null, _renderList(statusOptions, (status) => {
                    return _createVNode(_component_VListItem, {
                      key: status,
                      title: `${status}(${counts.value[status] || 0})`,
                      onClick: $event => (activeStatus.value = status)
                    }, null, 8 /* PROPS */, ["title", "onClick"])
                  }), 64 /* STABLE_FRAGMENT */))
                ]),
                _: 1 /* STABLE */
              })
            ]),
            _: 1 /* STABLE */
          }),
          _createVNode(_component_VBtn, {
            "prepend-icon": "mdi-checkbox-multiple-marked-outline",
            variant: multiSelect.value ? 'flat' : 'tonal',
            color: "primary",
            onClick: toggleMultiSelect
          }, {
            default: _withCtx(() => [
              _createTextVNode(_toDisplayString(multiSelect.value ? `完成(${selectedIds.value.length})` : '多选'), 1 /* TEXT */)
            ]),
            _: 1 /* STABLE */
          }, 8 /* PROPS */, ["variant"])
        ])
      ]),
      (loading.value)
        ? (_openBlock(), _createBlock(_component_VProgressLinear, {
            key: 1,
            indeterminate: "",
            color: "primary",
            class: "mb-3"
          }))
        : _createCommentVNode("v-if", true),
      (visibleItems.value.length)
        ? (_openBlock(), _createBlock(_component_VRow, {
            key: 2,
            dense: ""
          }, {
            default: _withCtx(() => [
              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(visibleItems.value, (item) => {
                return (_openBlock(), _createBlock(_component_VCol, {
                  key: item.id,
                  cols: "12",
                  sm: "6",
                  md: "4",
                  lg: "3"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VCard, {
                      class: _normalizeClass(["subscription-card", { selected: selectedIds.value.includes(item.id) }]),
                      variant: "flat",
                      onClick: $event => (toggleSelected(item.id))
                    }, {
                      default: _withCtx(() => [
                        _createElementVNode("div", _hoisted_6, [
                          _createElementVNode("div", _hoisted_7, [
                            (item.poster)
                              ? (_openBlock(), _createBlock(_component_VImg, {
                                  key: 0,
                                  src: item.poster,
                                  alt: item.title,
                                  width: "76",
                                  height: "114",
                                  contain: "",
                                  class: "poster-image"
                                }, null, 8 /* PROPS */, ["src", "alt"]))
                              : (_openBlock(), _createBlock(_component_VIcon, {
                                  key: 1,
                                  icon: "mdi-movie-open-outline",
                                  size: "34",
                                  color: "grey"
                                }))
                          ]),
                          _createElementVNode("div", _hoisted_8, [
                            _createElementVNode("div", _hoisted_9, [
                              (multiSelect.value)
                                ? (_openBlock(), _createBlock(_component_VCheckboxBtn, {
                                    key: 0,
                                    "model-value": selectedIds.value.includes(item.id),
                                    color: "primary",
                                    class: "me-1",
                                    onClick: _withModifiers($event => (toggleSelected(item.id)), ["stop"])
                                  }, null, 8 /* PROPS */, ["model-value", "onClick"]))
                                : _createCommentVNode("v-if", true),
                              _createElementVNode("div", {
                                class: "card-title",
                                title: item.title
                              }, _toDisplayString(item.title), 9 /* TEXT, PROPS */, _hoisted_10),
                              _createElementVNode("div", _hoisted_11, [
                                _createVNode(_component_VChip, {
                                  size: "small",
                                  variant: "flat",
                                  class: _normalizeClass(['status-badge', statusClass(item.status)]),
                                  title: "查看状态日志",
                                  onClick: _withModifiers($event => (showStatusLog(item)), ["stop"])
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(item.status), 1 /* TEXT */)
                                  ]),
                                  _: 2 /* DYNAMIC */
                                }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["class", "onClick"]),
                                _createVNode(_component_VBtn, {
                                  icon: "mdi-delete-outline",
                                  size: "x-small",
                                  variant: "text",
                                  color: "error",
                                  class: "delete-button",
                                  title: "删除订阅",
                                  onClick: _withModifiers($event => (askDelete(item)), ["stop"])
                                }, null, 8 /* PROPS */, ["onClick"])
                              ])
                            ]),
                            _createElementVNode("div", _hoisted_12, _toDisplayString(item.category) + " · " + _toDisplayString(item.subscribe_time), 1 /* TEXT */),
                            _createElementVNode("div", _hoisted_13, "发行年份：" + _toDisplayString(item.release_year || '-'), 1 /* TEXT */)
                          ])
                        ])
                      ]),
                      _: 2 /* DYNAMIC */
                    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["class", "onClick"])
                  ]),
                  _: 2 /* DYNAMIC */
                }, 1024 /* DYNAMIC_SLOTS */))
              }), 128 /* KEYED_FRAGMENT */))
            ]),
            _: 1 /* STABLE */
          }))
        : (!loading.value)
          ? (_openBlock(), _createBlock(_component_VAlert, {
              key: 3,
              type: "info",
              variant: "tonal"
            }, {
              default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                _createTextVNode("当前筛选条件下暂无订阅", -1 /* CACHED */)
              ]))]),
              _: 1 /* STABLE */
            }))
          : _createCommentVNode("v-if", true),
      _createElementVNode("div", _hoisted_14, [
        _createVNode(_component_VPagination, {
          modelValue: page.value,
          "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((page).value = $event)),
          length: totalPages.value,
          "total-visible": 5,
          density: "comfortable"
        }, null, 8 /* PROPS */, ["modelValue", "length"]),
        _createVNode(_component_VTextField, {
          modelValue: jumpPage.value,
          "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((jumpPage).value = $event)),
          modelModifiers: { number: true },
          type: "number",
          min: "1",
          max: totalPages.value,
          density: "compact",
          variant: "outlined",
          "hide-details": "",
          class: "jump-input",
          onKeyup: _withKeys(jump, ["enter"])
        }, null, 8 /* PROPS */, ["modelValue", "max"]),
        _createVNode(_component_VBtn, {
          color: "primary",
          variant: "tonal",
          onClick: jump
        }, {
          default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
            _createTextVNode("跳转", -1 /* CACHED */)
          ]))]),
          _: 1 /* STABLE */
        })
      ])
    ]),
    _createVNode(_component_VDialog, {
      modelValue: deleteDialog.value,
      "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((deleteDialog).value = $event)),
      "max-width": "480",
      persistent: ""
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCard, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "d-flex align-center ga-2" }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-alert-outline",
                  color: "warning"
                }),
                _cache[14] || (_cache[14] = _createTextVNode(" 删除订阅 ", -1 /* CACHED */))
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCardText, null, {
              default: _withCtx(() => [
                _createTextVNode(" 确认删除《" + _toDisplayString(pendingDelete.value?.title) + "》的订阅吗？这将同时取消插件中的订阅。 ", 1 /* TEXT */)
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCardActions, null, {
              default: _withCtx(() => [
                _createVNode(_component_VSpacer),
                _createVNode(_component_VBtn, {
                  variant: "text",
                  disabled: deleting.value,
                  onClick: _cache[4] || (_cache[4] = $event => (deleteDialog.value = false))
                }, {
                  default: _withCtx(() => [...(_cache[15] || (_cache[15] = [
                    _createTextVNode("取消", -1 /* CACHED */)
                  ]))]),
                  _: 1 /* STABLE */
                }, 8 /* PROPS */, ["disabled"]),
                _createVNode(_component_VBtn, {
                  color: "error",
                  variant: "flat",
                  loading: deleting.value,
                  onClick: confirmDelete
                }, {
                  default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
                    _createTextVNode("确认删除", -1 /* CACHED */)
                  ]))]),
                  _: 1 /* STABLE */
                }, 8 /* PROPS */, ["loading"])
              ]),
              _: 1 /* STABLE */
            })
          ]),
          _: 1 /* STABLE */
        })
      ]),
      _: 1 /* STABLE */
    }, 8 /* PROPS */, ["modelValue"]),
    _createVNode(_component_VDialog, {
      modelValue: logDialog.value,
      "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((logDialog).value = $event)),
      "max-width": "560"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCard, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "d-flex align-center ga-2" }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-text-box-search-outline",
                  color: "primary"
                }),
                _cache[17] || (_cache[17] = _createTextVNode(" 状态日志 ", -1 /* CACHED */))
              ]),
              _: 1 /* STABLE */
            }),
            (logItem.value)
              ? (_openBlock(), _createBlock(_component_VCardSubtitle, { key: 0 }, {
                  default: _withCtx(() => [
                    _createTextVNode("《" + _toDisplayString(logItem.value.title) + "》", 1 /* TEXT */)
                  ]),
                  _: 1 /* STABLE */
                }))
              : _createCommentVNode("v-if", true),
            _createVNode(_component_VCardText, { class: "log-content" }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(logItem.value?.error_log || '暂无详细错误日志'), 1 /* TEXT */)
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCardActions, null, {
              default: _withCtx(() => [
                _createVNode(_component_VSpacer),
                _createVNode(_component_VBtn, {
                  color: "primary",
                  variant: "tonal",
                  onClick: _cache[6] || (_cache[6] = $event => (logDialog.value = false))
                }, {
                  default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
                    _createTextVNode("关闭", -1 /* CACHED */)
                  ]))]),
                  _: 1 /* STABLE */
                })
              ]),
              _: 1 /* STABLE */
            })
          ]),
          _: 1 /* STABLE */
        })
      ]),
      _: 1 /* STABLE */
    }, 8 /* PROPS */, ["modelValue"]),
    _createVNode(_component_VSnackbar, {
      modelValue: snackbar.value,
      "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((snackbar).value = $event)),
      color: snackbarColor.value,
      timeout: "4500",
      location: "bottom"
    }, {
      actions: _withCtx(() => [
        _createVNode(_component_VBtn, {
          variant: "text",
          onClick: _cache[8] || (_cache[8] = $event => (snackbar.value = false))
        }, {
          default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
            _createTextVNode("关闭", -1 /* CACHED */)
          ]))]),
          _: 1 /* STABLE */
        })
      ]),
      default: _withCtx(() => [
        _createTextVNode(_toDisplayString(snackbarText.value) + " ", 1 /* TEXT */)
      ]),
      _: 1 /* STABLE */
    }, 8 /* PROPS */, ["modelValue", "color"])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-ae8bc53f"]]);

export { Page as default };
