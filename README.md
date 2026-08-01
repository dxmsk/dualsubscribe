# MoviePilot V2 双重订阅转发插件

仓库结构已经按 MoviePilot V2 第三方插件仓库规范准备：

```text
MoviePilot-DualSubscribe/
├── icons/
│   └── dualsubscribe.svg
├── plugins.v2/
│   └── dualsubscribe/
│       ├── __init__.py
│       ├── dist/assets/remoteEntry.js
│       ├── src/components/
│       └── README.md
└── package.v2.json
```

## 官方推荐安装：作为第三方插件市场仓库

依据 MoviePilot Wiki 的插件发布步骤：

1. Fork 官方 `jxxghp/MoviePilot-Plugins` 仓库，删除其它插件后放入本插件；也可以创建一个新的公开 GitHub 仓库，并将本目录内容上传到默认分支根目录。
2. 确认 GitHub 仓库根目录直接存在 `package.v2.json` 和 `plugins.v2/`，不要在外面再嵌套一层目录。
3. 将新仓库地址追加到 MoviePilot 的 `PLUGIN_MARKET`，多个仓库使用英文逗号分隔。不要覆盖掉原有官方仓库地址。
4. 完整重启或重建 MoviePilot 容器。
5. 进入“插件市场”刷新，搜索并安装“`双重订阅转发`”；安装完成后才会出现在“我的插件”。
6. 打开插件配置，启用后保存。

示例仓库地址：

```text
https://github.com/你的用户名/MoviePilot-DualSubscribe
```

`PLUGIN_MARKET` 示例（实际使用时在现有值末尾追加）：

```text
原有仓库地址,https://github.com/你的用户名/MoviePilot-DualSubscribe
```

MoviePilot V2 会读取仓库根目录的 `package.v2.json` 和 `plugins.v2/`。

## 开发方式：V2 本地插件仓库

MoviePilot V2 不会把 `/config/plugins` 当作插件源码目录。该目录是插件运行数据目录，直接复制 `dualsubscribe` 到其中不会显示插件。

只有当前 MoviePilot 版本支持 `PLUGIN_LOCAL_REPO_PATHS` 时才使用此方式。在 fnOS 上可以把本仓库解压为：

```text
/vol2/1000/Docker/MoviePilot/config/local-plugins/
├── icons/
│   └── dualsubscribe.svg
├── plugins.v2/
│   └── dualsubscribe/
│       ├── __init__.py
│       ├── dualsubscribe.svg
│       └── README.md
└── package.v2.json
```

如果宿主机的 `config` 已映射为容器内 `/config`，在 MoviePilot 容器增加环境变量：

```text
PLUGIN_LOCAL_REPO_PATHS=/config/local-plugins
PLUGIN_AUTO_RELOAD=true
```

完整重启 MoviePilot 后，进入“插件市场”搜索“`双重订阅转发`”或“`DualSubscribe`”，点击安装。安装动作会把插件写入 MoviePilot 的已安装插件列表并将代码同步到实际运行目录；随后才会出现在“我的插件”中。

如果市场中仍然没有显示，先在容器终端确认以下三个路径都存在：

```text
/config/local-plugins/package.v2.json
/config/local-plugins/plugins.v2/dualsubscribe/__init__.py
/config/local-plugins/icons/dualsubscribe.svg
```

## 默认配置

- 插件首次安装默认关闭，防止未确认前产生外部请求。
- 用户指定的接口已作为默认外部订阅地址写入配置。
- 默认使用 `POST` + JSON，并发送与 MoviePilot 新增订阅 API 相同的 TMDB 订阅字段。
- 目标接口会立即添加订阅，不受本地延迟影响。
- MoviePilot 本地新订阅会按用户设置的分钟数暂停，再自动恢复为订阅中；默认 30 分钟，重启后会继续未完成的计时。
- 插件主页面只展示 ID、电影名、分类、订阅时间、发行年份和四种标准状态。
- 顶部支持状态数量统计、点击筛选和多选；底部支持分页、页码输入与跳转。
- MoviePilot 恢复暂停订阅前检查已启用的 Emby；确认电影或当前电视剧订阅范围完整入库后，直接取消 MP 本地订阅。
- 可选在 MoviePilot 自动订阅搜索任务开始前再次同步对应 TMDB 订阅。
- 外部请求失败会记录状态，但本地订阅仍按用户设置的延迟时间恢复。

详细请求格式与验证方法见 `plugins.v2/dualsubscribe/README.md`。
