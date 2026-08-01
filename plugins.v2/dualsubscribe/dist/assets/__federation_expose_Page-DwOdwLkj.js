import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const _export_sfc = (sfc, props) => {
  const target = sfc.__vccOpts || sfc;
  for (const [key, val] of props) {
    target[key] = val;
  }
  return target;
};

const {createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,mergeProps:_mergeProps,withModifiers:_withModifiers,normalizeClass:_normalizeClass,withKeys:_withKeys} = await importShared('vue');


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
const _hoisted_11 = { class: "meta-line" };
const _hoisted_12 = { class: "meta-line" };
const _hoisted_13 = { class: "pagination-row mt-5" };

const {computed,onMounted,ref,watch} = await importShared('vue');


const pageSize = 12;


const _sfc_main = {
  __name: 'Page',
  props: {
  api: {
    type: Object,
    default: () => ({}),
  },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const statusOptions = ['已暂停', '双重订阅', '未识别', '异常'];
const statusMeta = {
  已暂停: { color: 'orange-darken-2', icon: 'mdi-pause-circle-outline' },
  双重订阅: { color: 'indigo-accent-2', icon: 'mdi-bell-ring-outline' },
  未识别: { color: 'amber-accent-4', icon: 'mdi-help-circle-outline' },
  异常: { color: 'red-accent-3', icon: 'mdi-alert-circle-outline' },
};

const items = ref([]);
const loading = ref(false);
const error = ref('');
const activeStatus = ref(null);
const multiSelect = ref(false);
const selectedIds = ref([]);
const page = ref(1);
const jumpPage = ref(1);
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

async function loadItems() {
  loading.value = true;
  error.value = '';
  try {
    const response = await props.api.get('plugin/DualSubscribe/items');
    const data = unwrapResponse(response);
    items.value = Array.isArray(data) ? data : [];
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

function jump() {
  const target = Math.max(1, Math.min(Number(jumpPage.value) || 1, totalPages.value));
  page.value = target;
  jumpPage.value = target;
}

watch([activeStatus, () => items.value.length], () => {
  page.value = 1;
  jumpPage.value = 1;
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

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-2"
    }, {
      default: _withCtx(() => [
        _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-h6 font-weight-bold" }, "双重订阅", -1 /* CACHED */)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          icon: "mdi-refresh",
          variant: "text",
          loading: loading.value,
          onClick: loadItems
        }, null, 8 /* PROPS */, ["loading"]),
        _createVNode(_component_VBtn, {
          icon: "mdi-close",
          variant: "text",
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
              color: statusMeta[status].color,
              variant: activeStatus.value === status ? 'flat' : 'tonal',
              "prepend-icon": statusMeta[status].icon,
              class: "status-pill",
              onClick: $event => (toggleStatus(status))
            }, {
              default: _withCtx(() => [
                _createTextVNode(_toDisplayString(status) + "(" + _toDisplayString(counts.value[status] || 0) + ") ", 1 /* TEXT */)
              ]),
              _: 2 /* DYNAMIC */
            }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["color", "variant", "prepend-icon", "onClick"])
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
                default: _withCtx(() => [...(_cache[5] || (_cache[5] = [
                  _createTextVNode(" 筛选 ", -1 /* CACHED */)
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
                              _createVNode(_component_VChip, {
                                size: "small",
                                variant: "flat",
                                class: _normalizeClass(['status-badge', statusClass(item.status)])
                              }, {
                                default: _withCtx(() => [
                                  _createTextVNode(_toDisplayString(item.status), 1 /* TEXT */)
                                ]),
                                _: 2 /* DYNAMIC */
                              }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["class"])
                            ]),
                            _createElementVNode("div", _hoisted_11, _toDisplayString(item.category) + " · " + _toDisplayString(item.subscribe_time), 1 /* TEXT */),
                            _createElementVNode("div", _hoisted_12, "发行年份：" + _toDisplayString(item.release_year || '-'), 1 /* TEXT */)
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
              default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
                _createTextVNode("当前筛选条件下暂无订阅", -1 /* CACHED */)
              ]))]),
              _: 1 /* STABLE */
            }))
          : _createCommentVNode("v-if", true),
      _createElementVNode("div", _hoisted_13, [
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
          default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
            _createTextVNode("跳转", -1 /* CACHED */)
          ]))]),
          _: 1 /* STABLE */
        })
      ])
    ])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-9125e06a"]]);

export { Page as default };
