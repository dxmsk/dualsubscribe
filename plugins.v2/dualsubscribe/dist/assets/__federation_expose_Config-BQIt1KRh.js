import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {createElementVNode:_createElementVNode,resolveComponent:_resolveComponent,createVNode:_createVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,openBlock:_openBlock,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "dual-config" };

const {onMounted,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
},
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;

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
});

function saveConfig() {
  const payload = {
    ...config.value,
    timeout: Math.max(1, Math.min(Number(config.value.timeout) || 10, 60)),
    pause_minutes: Math.max(1, Math.min(Number(config.value.pause_minutes) || 30, 10080)),
  };
  emit('save', payload);
}

onMounted(() => {
  config.value = {
    ...config.value,
    ...(props.initialConfig || {}),
  };
});

return (_ctx, _cache) => {
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VTextarea = _resolveComponent("VTextarea");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VContainer = _resolveComponent("VContainer");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent"
    }, {
      default: _withCtx(() => [
        _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-h6 ms-3" }, "双重订阅配置", -1 /* CACHED */)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          icon: "mdi-content-save",
          color: "primary",
          variant: "text",
          onClick: saveConfig
        }),
        _createVNode(_component_VBtn, {
          icon: "mdi-close",
          variant: "text",
          onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
        })
      ]),
      _: 1 /* STABLE */
    }),
    _createVNode(_component_VDivider),
    _createVNode(_component_VContainer, { class: "pt-5" }, {
      default: _withCtx(() => [
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VSwitch, {
                  modelValue: config.value.enabled,
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.value.enabled) = $event)),
                  label: "启用插件",
                  color: "primary"
                }, null, 8 /* PROPS */, ["modelValue"])
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.value.pause_minutes,
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.value.pause_minutes) = $event)),
                  modelModifiers: { number: true },
                  type: "number",
                  min: "1",
                  max: "10080",
                  label: "本地暂停时间（分钟）",
                  hint: "仅影响保存后新增的订阅",
                  "persistent-hint": ""
                }, null, 8 /* PROPS */, ["modelValue"])
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "4"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.value.timeout,
                  "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.value.timeout) = $event)),
                  modelModifiers: { number: true },
                  type: "number",
                  min: "1",
                  max: "60",
                  label: "接口超时（秒）"
                }, null, 8 /* PROPS */, ["modelValue"])
              ]),
              _: 1 /* STABLE */
            })
          ]),
          _: 1 /* STABLE */
        }),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.value.username,
                  "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.value.username) = $event)),
                  label: "目标 MoviePilot 用户名",
                  autocomplete: "username"
                }, null, 8 /* PROPS */, ["modelValue"])
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.value.password,
                  "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.value.password) = $event)),
                  label: "目标 MoviePilot 密码",
                  type: "password",
                  autocomplete: "current-password"
                }, null, 8 /* PROPS */, ["modelValue"])
              ]),
              _: 1 /* STABLE */
            })
          ]),
          _: 1 /* STABLE */
        }),
        _createVNode(_component_VTextField, {
          modelValue: config.value.endpoint,
          "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.value.endpoint) = $event)),
          label: "外部 MoviePilot 兼容订阅接口",
          placeholder: "http://host/path/api/v1/subscribe/",
          disabled: !config.value.primary_enabled
        }, null, 8 /* PROPS */, ["modelValue", "disabled"]),
        _createVNode(_component_VSwitch, {
          modelValue: config.value.primary_enabled,
          "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.value.primary_enabled) = $event)),
          label: "同步兼容 MoviePilot 目标",
          color: "primary",
          hint: "29999 代理不返回订阅 ID 时，可关闭此项并只使用下方附加接口",
          "persistent-hint": ""
        }, null, 8 /* PROPS */, ["modelValue"]),
        _createVNode(_component_VTextarea, {
          modelValue: config.value.headers,
          "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.value.headers) = $event)),
          label: "额外请求头（JSON，可选）",
          rows: "3",
          placeholder: "{\"Authorization\": \"Bearer ...\"}",
          disabled: !config.value.primary_enabled
        }, null, 8 /* PROPS */, ["modelValue", "disabled"]),
        _createVNode(_component_VSwitch, {
          modelValue: config.value.sync_before_auto_search,
          "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.value.sync_before_auto_search) = $event)),
          label: "MoviePilot 自动搜索前再次同步目标端",
          color: "primary"
        }, null, 8 /* PROPS */, ["modelValue"]),
        _createVNode(_component_VDivider, { class: "my-5" }),
        _cache[18] || (_cache[18] = _createElementVNode("div", { class: "text-subtitle-1 font-weight-bold mb-3" }, "附加订阅接口（3300）", -1 /* CACHED */)),
        _createVNode(_component_VSwitch, {
          modelValue: config.value.secondary_enabled,
          "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.value.secondary_enabled) = $event)),
          label: "同时提交到附加订阅接口",
          color: "primary",
          hint: "开启后新增订阅会同时调用 /api/v1/subscription/create",
          "persistent-hint": ""
        }, null, 8 /* PROPS */, ["modelValue"]),
        _createVNode(_component_VTextField, {
          modelValue: config.value.secondary_endpoint,
          "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.value.secondary_endpoint) = $event)),
          label: "附加接口新增 URL",
          placeholder: "http://host:3300/api/v1/subscription/create",
          disabled: !config.value.secondary_enabled
        }, null, 8 /* PROPS */, ["modelValue", "disabled"]),
        _createVNode(_component_VTextField, {
          modelValue: config.value.secondary_token,
          "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.value.secondary_token) = $event)),
          label: "附加接口 Bearer Token",
          type: "password",
          autocomplete: "off",
          hint: "只填写 Token 内容，不要包含 Bearer 前缀",
          "persistent-hint": "",
          disabled: !config.value.secondary_enabled
        }, null, 8 /* PROPS */, ["modelValue", "disabled"]),
        _createVNode(_component_VRow, null, {
          default: _withCtx(() => [
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.value.secondary_account_id,
                  "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.value.secondary_account_id) = $event)),
                  label: "附加接口账号 ID",
                  disabled: !config.value.secondary_enabled
                }, null, 8 /* PROPS */, ["modelValue", "disabled"])
              ]),
              _: 1 /* STABLE */
            }),
            _createVNode(_component_VCol, {
              cols: "12",
              md: "6"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VTextField, {
                  modelValue: config.value.secondary_target_directory,
                  "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.value.secondary_target_directory) = $event)),
                  label: "目标目录",
                  placeholder: "/待整理",
                  disabled: !config.value.secondary_enabled
                }, null, 8 /* PROPS */, ["modelValue", "disabled"])
              ]),
              _: 1 /* STABLE */
            })
          ]),
          _: 1 /* STABLE */
        }),
        _createVNode(_component_VTextField, {
          modelValue: config.value.secondary_quality_preference,
          "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.value.secondary_quality_preference) = $event)),
          label: "画质偏好",
          placeholder: "1080p",
          disabled: !config.value.secondary_enabled
        }, null, 8 /* PROPS */, ["modelValue", "disabled"]),
        _createVNode(_component_VAlert, {
          type: "info",
          variant: "tonal",
          class: "mt-3"
        }, {
          default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
            _createTextVNode(" 兼容 MP 目标和附加接口都会立即订阅；删除卡片时会按各自保存或回查到的 ID 联动取消。Token 不会写入插件日志。 ", -1 /* CACHED */)
          ]))]),
          _: 1 /* STABLE */
        })
      ]),
      _: 1 /* STABLE */
    })
  ]))
}
}

};

export { _sfc_main as default };
