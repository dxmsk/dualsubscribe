# 双重订阅转发

适用于 MoviePilot V2。插件监听 `EventType.SubscribeAdded`，读取刚创建的完整订阅记录，然后向配置的外部地址发送一次兼容 MoviePilot 新增订阅 API 的 `POST` JSON 请求。目标接口只支持 TMDB，因此没有有效 `tmdbid` 的订阅会被跳过。

## 安装

请将插件随 `package.v2.json` 和 `plugins.v2/` 发布到一个 GitHub 仓库，并将仓库地址追加到 MoviePilot 的 `PLUGIN_MARKET`。然后到“插件市场”安装本插件。

`/config/plugins` 是 MoviePilot 的插件数据目录，不是插件源码目录，直接复制到该目录不会显示。支持 `PLUGIN_LOCAL_REPO_PATHS` 的新版 MoviePilot 也可以保留以下仓库结构进行本地开发：

```text
/config/local-plugins/
├── package.v2.json
├── icons/dualsubscribe.svg
└── plugins.v2/dualsubscribe/__init__.py
```

```text
PLUGIN_LOCAL_REPO_PATHS=/config/local-plugins
PLUGIN_AUTO_RELOAD=true
```

完整重启 MoviePilot 后，到“插件市场”搜索并安装 `DualSubscribe`，然后回到“我的插件”启用。直接把插件目录复制到 `/config/plugins` 不会被 MoviePilot 扫描。

## 请求格式

插件发送的字段与 MoviePilot 的 `POST /api/v1/subscribe/` 一致，例如：

```json
{
  "name": "示例剧集",
  "year": "2026",
  "type": "电视剧",
  "tmdbid": 12345,
  "media_source": "themoviedb",
  "media_id": "12345",
  "season": 1,
  "sites": [],
  "filter_groups": []
}
```

实际请求还会复制原订阅的过滤规则、质量、分辨率、包含/排除、下载器、保存路径和洗版设置等公共写入字段。接口地址必须填写完整 URL；如果目标需要 `Authorization`，可通过“额外请求头”配置。

用户提供的令牌基础地址会自动补全 MoviePilot 新增订阅路由，最终请求地址为：

```text
http://192.168.1.6:29999/mp/<令牌>/api/v1/subscribe/
```

插件会先用配置的用户名和密码请求同一前缀下的登录接口：

```text
http://192.168.1.6:29999/mp/<令牌>/api/v1/login/access-token
```

登录成功后使用返回的 Bearer Token 调用订阅接口。Token 仅缓存在插件进程内存中，收到 401 时会重新登录并重试一次。

插件还会转发源订阅已经保存的 `poster`、`backdrop`、`vote` 和 `description`，供目标代理直接使用。

## 用户设置本地延迟分钟数

对于有效的 TMDB 新订阅，插件会先把 MoviePilot 本地状态从 `N` 改成 `S`（暂停），目标接口仍会立即收到订阅请求。达到用户设置的分钟数后，插件仅在本地订阅仍为 `S` 时将其改成 `R`（订阅中）。配置范围为 1～10080 分钟，默认 30 分钟。

- 延迟任务会持久化，MoviePilot 在等待期间重启后会继续执行。
- 如果用户提前手动恢复或改成其它状态，定时任务不会覆盖用户选择。
- 如果停用插件，尚未到期且仍处于暂停状态的订阅会立即恢复。
- 自动恢复暂时失败时，会在 1 分钟后重试。

插件详情页会保存全部插件订阅记录，以紧凑横向海报卡片按添加时间倒序展示。桌面端每行四列，平板每行两列，手机每行一列。海报在左、订阅信息在右，海报底部显示状态角标；点击海报会在新页面打开对应 TMDB 详情。

## 自动搜索前再次同步

开启“自动搜索前再次同步”后，插件会在 MoviePilot 的两个系统自动任务开始前执行：

- `new_subscribe_search`：同步所有状态为 `N` 的 TMDB 订阅，然后开始新增订阅搜索。
- `subscribe_search`：同步所有状态为 `R` 的 TMDB 订阅，然后开始订阅搜索补全。

手动点击搜索不会触发这项批量同步。前置同步为串行请求，MoviePilot 会等待接口同步结束后再开始搜索。

## 行为说明

- 每个新增订阅事件请求一次；开启自动搜索前同步后，系统自动搜索任务会再次提交对应订阅。
- 仅发送有效的 TMDB ID，不会将豆瓣、Bangumi 或 AniList ID 作为 TMDB ID 使用。
- 外部接口超时、返回 4xx/5xx，或返回 `{"success": false}` 时会写入 MoviePilot 日志和海报卡片状态，不删除本地订阅；本地仍会在用户设置的延迟时间后恢复。
- 默认超时 10 秒，可在 1～60 秒之间调整。
- 可用 JSON 对象配置额外请求头。
- 接口地址中可能包含访问令牌，插件不会在日志中打印完整路径。
- 错误日志会记录目标响应的前 500 个字符，便于判断路由或参数问题。

## 验证

启用插件并保存后，在 MoviePilot 中添加一个测试订阅，然后在 MoviePilot 日志中搜索“`双重订阅转发`”。成功日志会包含 HTTP 状态码；失败日志会包含目标主机、错误类型和可用的 HTTP 状态码，但不会记录含令牌的完整接口路径。
