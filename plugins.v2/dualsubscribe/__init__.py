import json
from datetime import datetime, timedelta
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from app.chain.mediaserver import MediaServerChain
from app.core.config import settings
from app.core.context import MediaInfo
from app.core.event import eventmanager
from app.db.subscribe_oper import SubscribeOper
from app.helper.mediaserver import MediaServerHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, MediaType


class DualSubscribe(_PluginBase):
    """将 MoviePilot 新增订阅同步到兼容 MoviePilot API 的外部接口。"""

    plugin_name = "双重订阅转发"
    plugin_desc = "双重订阅、联动取消、延迟恢复、Emby 完成检查与状态管理。"
    plugin_icon = "dualsubscribe.svg"
    plugin_version = "1.8.1"
    plugin_author = "Codex"
    author_url = ""
    plugin_config_prefix = "dualsubscribe_"
    plugin_order = 30
    auth_level = 1

    ENDPOINT_BASE = (
        "http://192.168.1.6:29999/mp/"
        "f1a20bf6399b1d0c1e32b5206eaf6ee63821d69dee5cf73d84cf6612b969eb7e"
    )
    DEFAULT_ENDPOINT = f"{ENDPOINT_BASE}/api/v1/subscribe/"
    DEFAULT_PAUSE_MINUTES = 30
    HISTORY_KEY = "subscribe_history"
    PENDING_KEY = "pending_resumes"

    # MoviePilot POST /api/v1/subscribe/ 接受的公共写入字段。
    API_WRITE_FIELDS = {
        "name", "year", "type", "keyword", "tmdbid", "doubanid",
        "bangumiid", "anilistid", "mediaid", "media_source", "media_id",
        "season", "filter", "include", "exclude", "quality", "resolution",
        "effect", "total_episode", "start_episode", "sites", "downloader",
        "best_version", "best_version_full", "save_path", "search_imdbid",
        "custom_words", "media_category", "filter_groups", "episode_group",
        # MoviePilot 写入时会忽略这些运行字段，但目标代理可直接使用它们，
        # 避免再次通过外部元数据 API 补全海报和简介。
        "poster", "backdrop", "vote", "description",
    }

    _enabled = False
    _endpoint = DEFAULT_ENDPOINT
    _timeout = 10
    _pause_minutes = DEFAULT_PAUSE_MINUTES
    _username = "admin"
    _password = "admin"
    _access_token = ""
    _sync_before_auto_search = False
    _headers: Dict[str, str] = {}
    _scheduler: Optional[BackgroundScheduler] = None
    _data_lock = RLock()

    def init_plugin(self, config: dict = None) -> None:
        """读取配置、恢复延迟任务并安装自动搜索钩子。"""
        self.stop_service()
        config = config or {}
        self._enabled = bool(config.get("enabled", False))
        self._endpoint = self.__normalize_endpoint(
            str(config.get("endpoint") or self.DEFAULT_ENDPOINT).strip()
        )
        self._timeout = self.__safe_timeout(config.get("timeout", 10))
        self._pause_minutes = self.__safe_pause_minutes(
            config.get("pause_minutes", self.DEFAULT_PAUSE_MINUTES)
        )
        self._username = str(config.get("username") or "admin").strip()
        self._password = str(config.get("password") or "admin")
        self._access_token = ""
        self._sync_before_auto_search = bool(config.get("sync_before_auto_search", False))
        self._headers = self.__parse_headers(config.get("headers"))
        self.__configure_search_hook()
        if self._enabled:
            self.__start_resume_scheduler()
            self.__restore_pending_resumes()
        else:
            self.__resume_all_pending(reason="插件已停用")

    def get_state(self) -> bool:
        """返回插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件远程命令列表。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """返回 Vue 主页面使用的查询和联动取消 API。"""
        return [{
            "path": "/items",
            "endpoint": self.api_items,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "查询双重订阅极简列表",
        }, {
            "path": "/unsubscribe/{subscribe_id}",
            "endpoint": self.api_unsubscribe,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "取消 MP 与目标端订阅并删除插件记录",
        }]

    @staticmethod
    def get_render_mode() -> Tuple[str, str]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def api_items(self) -> List[Dict[str, Any]]:
        """返回包含极简字段和海报地址且按订阅时间倒序排列的数据。"""
        items = []
        history = sorted(
            self.__get_history(),
            key=lambda value: value.get("time") or "",
            reverse=True,
        )
        for index, item in enumerate(history, start=1):
            status = self.__status_value(item)
            items.append({
                "id": int(item.get("subscribe_id") or index),
                "title": str(item.get("title") or "未知电影"),
                "category": self.__category_value(item),
                "subscribe_time": self.__minute_time(item.get("time")),
                "release_year": self.__release_year(item.get("year")),
                "status": status,
                "poster": str(item.get("poster") or ""),
                "error_log": self.__error_log_value(item, status),
            })
        return items

    def api_unsubscribe(self, subscribe_id: int) -> Dict[str, Any]:
        """联动取消本地和目标订阅；无论远端结果如何都永久删除插件记录。"""
        subscribe_id = int(subscribe_id)
        history = self.__get_history()
        history_item = next(
            (
                item for item in history
                if int(item.get("subscribe_id") or 0) == subscribe_id
            ),
            None,
        )
        if not history_item:
            return {
                "success": True,
                "local_success": True,
                "plugin_success": True,
                "message": "订阅记录已不存在",
            }

        local_success = True
        local_error = ""
        try:
            subscribe = SubscribeOper().get(subscribe_id)
            if subscribe:
                SubscribeOper().delete(subscribe_id)
                logger.info(f"双重订阅取消：MP 本地订阅已取消，subscribe_id={subscribe_id}")
        except Exception as err:
            local_success = False
            local_error = str(err) or type(err).__name__
            logger.exception(
                f"双重订阅取消：MP 本地订阅取消失败，subscribe_id={subscribe_id}, error={err}"
            )

        plugin_success, plugin_error = self.__cancel_linked_subscription(
            subscribe_id=subscribe_id,
            history_item=history_item,
            origin="插件页面删除",
        )

        issues = []
        if not local_success:
            issues.append(f"MP 取消失败：{local_error}")
        if not plugin_success:
            issues.append(f"插件取消失败：{plugin_error}")
        if issues:
            message = "；".join(issues) + "，已强制移除本地记录"
            logger.warning(f"双重订阅取消：subscribe_id={subscribe_id}, {message}")
        else:
            message = "MP 与插件订阅均已取消"

        return {
            "success": True,
            "local_success": local_success,
            "plugin_success": plugin_success,
            "message": message,
        }

    def __cancel_linked_subscription(
        self,
        subscribe_id: int,
        history_item: Optional[Dict[str, Any]] = None,
        origin: str = "MP 取消订阅",
    ) -> Tuple[bool, str]:
        """取消目标端订阅并永久清除插件历史和待恢复任务。"""
        subscribe_id = int(subscribe_id)
        if history_item is None:
            history_item = next(
                (
                    item for item in self.__get_history()
                    if int(item.get("subscribe_id") or 0) == subscribe_id
                ),
                None,
            )
        if not history_item:
            return True, ""

        target_status = str(history_item.get("target_status") or "")
        if not history_item.get("tmdbid") or "跳过" in target_status:
            plugin_success, plugin_error = True, ""
        else:
            target_subscribe_id = self.__positive_int(
                history_item.get("target_subscribe_id")
            )
            if target_subscribe_id:
                plugin_success, plugin_error = self.__unsubscribe_target(
                    target_subscribe_id=target_subscribe_id,
                    source_subscribe_id=subscribe_id,
                )
            else:
                plugin_success, plugin_error = self.__unsubscribe_target_media(
                    history_item=history_item,
                    source_subscribe_id=subscribe_id,
                )

        # 页面记录不能因目标端错误重新出现，恢复任务也必须同步清除。
        self.__remove_pending_resume(subscribe_id)
        with self._data_lock:
            remaining = [
                item for item in self.__get_history()
                if int(item.get("subscribe_id") or 0) != subscribe_id
            ]
            self.save_data(self.HISTORY_KEY, remaining)

        if plugin_success:
            logger.info(
                f"双重订阅联动清理完成：origin={origin}, subscribe_id={subscribe_id}"
            )
        else:
            logger.warning(
                f"双重订阅联动清理：origin={origin}, subscribe_id={subscribe_id}, "
                f"插件取消失败={plugin_error}，已移除插件记录"
            )
        return plugin_success, plugin_error

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """Vue 模式下返回空页面结构与默认配置模型。"""
        return [], {
            "enabled": False,
            "endpoint": self.DEFAULT_ENDPOINT,
            "timeout": 10,
            "pause_minutes": self.DEFAULT_PAUSE_MINUTES,
            "username": "admin",
            "password": "admin",
            "sync_before_auto_search": False,
            "headers": "",
        }

        # 以下结构仅保留用于旧版 MoviePilot 回退，不会在 Vue 模式下执行。
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout",
                                            "label": "请求超时（秒）",
                                            "type": "number",
                                            "min": 1,
                                            "max": 60,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "pause_minutes",
                                            "label": "本地暂停时间（分钟）",
                                            "type": "number",
                                            "min": 1,
                                            "max": 10080,
                                            "hint": "仅影响保存配置后新增的订阅",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "sync_before_auto_search",
                                            "label": "自动搜索前再次同步",
                                            "hint": "在新增订阅搜索和订阅搜索补全任务开始前，先同步对应状态的 TMDB 订阅",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "username",
                                            "label": "目标 MoviePilot 用户名",
                                            "autocomplete": "username",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "password",
                                            "label": "目标 MoviePilot 密码",
                                            "type": "password",
                                            "autocomplete": "current-password",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "endpoint",
                                            "label": "外部 MoviePilot 兼容订阅接口",
                                            "placeholder": "http://host/path",
                                            "hint": "填写完整 URL；插件会发送与 MoviePilot 新增订阅 API 相同的 POST JSON 请求体",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "headers",
                                            "label": "额外请求头（JSON，可选）",
                                            "rows": 3,
                                            "placeholder": '{"Authorization": "Bearer ..."}',
                                            "hint": "必须是 JSON 对象；无需手动填写 Content-Type",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VAlert",
                        "props": {
                            "type": "info",
                            "variant": "tonal",
                            "text": (
                                "仅处理带有效 TMDB ID 的订阅。目标端会立即订阅；"
                                "MoviePilot 本地订阅会按设置的分钟数暂停，再自动恢复为订阅中。"
                                "开启“自动搜索前再次同步”后，自动搜索会等待接口同步完成后再开始。"
                            ),
                        },
                    },
                ],
            }
        ], {
            "enabled": False,
            "endpoint": self.DEFAULT_ENDPOINT,
            "timeout": 10,
            "pause_minutes": self.DEFAULT_PAUSE_MINUTES,
            "username": "admin",
            "password": "admin",
            "sync_before_auto_search": False,
            "headers": "",
        }

    def get_page(self) -> List[dict]:
        """Vue 模式下主页面由远程 Page 组件渲染。"""
        return []

        # 以下结构仅保留用于旧版 MoviePilot 回退，不会在 Vue 模式下执行。
        history = self.__get_history()
        if not history:
            return [{
                "component": "VAlert",
                "props": {
                    "type": "info",
                    "variant": "tonal",
                    "text": "暂无新增订阅记录",
                },
            }]

        cards = []
        for item in sorted(history, key=lambda value: value.get("time") or "", reverse=True):
            tmdbid = item.get("tmdbid")
            media_path = "tv" if item.get("type") == "电视剧" else "movie"
            details_url = (
                f"https://www.themoviedb.org/{media_path}/{tmdbid}"
                if tmdbid else "#"
            )
            badge_text, badge_color, badge_icon = self.__status_badge(item)
            if item.get("poster"):
                poster = {
                    "component": "VImg",
                    "props": {
                        "src": item.get("poster"),
                        "width": 88,
                        "height": 132,
                        "aspect-ratio": "2/3",
                        "cover": True,
                        "class": "rounded cursor-pointer",
                    },
                }
            else:
                poster = {
                    "component": "VSheet",
                    "props": {
                        "width": 88,
                        "height": 132,
                        "class": "d-flex align-center justify-center rounded",
                        "color": "surface-variant",
                    },
                    "content": [{
                        "component": "VIcon",
                        "props": {"icon": "mdi-movie-open", "size": 40},
                    }],
                }

            poster_block = {
                "component": "a",
                "props": {
                    "href": details_url,
                    "target": "_blank",
                    "title": "点击查看 TMDB 详情",
                    "class": "text-decoration-none flex-shrink-0",
                },
                "content": [{
                    "component": "div",
                    "props": {"class": "position-relative"},
                    "content": [poster, {
                        "component": "VChip",
                        "props": {
                            "size": "x-small",
                            "color": badge_color,
                            "variant": "flat",
                            "prepend-icon": badge_icon,
                            "class": "position-absolute bottom-0 left-0 ma-1",
                        },
                        "text": badge_text,
                    }],
                }],
            }
            info_block = {
                "component": "div",
                "props": {
                    "class": "ps-3 py-1 flex-grow-1 overflow-hidden",
                    "style": "min-width: 0",
                },
                "content": [{
                    "component": "div",
                    "props": {
                        "class": "text-body-2 font-weight-bold text-truncate mb-2",
                        "title": item.get("title") or "未知标题",
                    },
                    "text": item.get("title") or "未知标题",
                },
                    self.__detail_line("mdi-shape-outline", f"类型  {self.__media_subtitle(item)}"),
                    self.__detail_line("mdi-robot-outline", "来源  双重订阅转发"),
                    self.__detail_line("mdi-clock-outline", f"订阅时间  {item.get('time') or '-'}"),
                    self.__detail_line("mdi-calendar-outline", f"发行年份  {item.get('year') or '-'}"),
                    self.__detail_line("mdi-cloud-check-outline", item.get("target_status") or "-"),
                ],
            }
            cards.append({
                "component": "VCol",
                "props": {"cols": 12, "sm": 6, "lg": 3},
                "content": [{
                    "component": "VCard",
                    "props": {
                        "variant": "flat",
                        "height": 148,
                        "class": "border rounded pa-2",
                        "title": (
                            f"{item.get('title') or '未知标题'}\n"
                            f"目标端：{item.get('target_status') or '-'}\n"
                            f"本地：{item.get('local_status') or '-'}"
                        ),
                    },
                    "content": [{
                        "component": "div",
                        "props": {"class": "d-flex align-start"},
                        "content": [poster_block, info_block],
                    }],
                }],
            })

        return [{
            "component": "div",
            "props": {"class": "d-flex align-center justify-space-between mb-2 px-1"},
            "content": [{
                "component": "div",
                "props": {"class": "text-subtitle-1 font-weight-medium"},
                "text": "最近订阅",
            }, {
                "component": "VChip",
                "props": {"size": "small", "variant": "tonal"},
                "text": f"共 {len(history)} 条",
            }],
        }, {
            "component": "VRow",
            "props": {"dense": True},
            "content": cards,
        }]

    @eventmanager.register(EventType.SubscribeAdded)
    def forward_subscription(self, event) -> None:
        """暂停本地新订阅，并立即按 MoviePilot API 格式转发到目标端。"""
        if not self._enabled or not self._endpoint:
            return
        if not event:
            return

        event_data = event.event_data if isinstance(event.event_data, dict) else {}
        subscribe_id = event_data.get("subscribe_id")
        if not subscribe_id:
            logger.error("双重订阅转发失败：新增订阅事件中没有 subscribe_id")
            return

        try:
            subscribe = SubscribeOper().get(int(subscribe_id))
        except Exception as err:
            logger.exception(f"双重订阅转发失败：读取订阅 {subscribe_id} 时出错：{err}")
            return
        if not subscribe:
            logger.error(f"双重订阅转发失败：找不到订阅 {subscribe_id}")
            return

        tmdbid = self.__valid_tmdbid(subscribe)
        conversion_error = ""
        if not tmdbid:
            tmdbid, conversion_error = self.__resolve_douban_tmdbid(subscribe)
        if not tmdbid:
            self.__save_subscribe_history(
                subscribe,
                target_status="已跳过（缺少有效 TMDB ID）",
                local_status="MP 本地未暂停",
                error_log=conversion_error or "缺少有效 TMDB ID，目标接口仅支持 TMDB ID",
            )
            logger.warning(
                f"双重订阅转发跳过：subscribe_id={subscribe_id}, "
                f"name={getattr(subscribe, 'name', '-')}, "
                f"原因={conversion_error or '目标接口仅支持 TMDB ID'}"
            )
            return

        resume_at, local_status = self.__pause_local_subscription(subscribe)
        self.__save_subscribe_history(
            subscribe,
            target_status="等待目标端同步",
            local_status=local_status,
            resume_at=resume_at,
            resolved_tmdbid=tmdbid,
        )
        result = self.__forward_record(
            subscribe,
            trigger="新增订阅",
            resolved_tmdbid=tmdbid,
        )
        self.__save_subscribe_history(
            subscribe,
            target_status="目标端同步成功" if result["success"] else "目标端同步失败",
            local_status=local_status,
            resume_at=resume_at,
            error_log=result["error_log"],
            target_subscribe_id=result["target_subscribe_id"],
            resolved_tmdbid=tmdbid,
        )

    @eventmanager.register(EventType.SubscribeDeleted)
    def remove_linked_subscription(self, event) -> None:
        """MP 中取消订阅时同步取消目标端订阅并清除插件页面记录。"""
        if not self._enabled or not event:
            return
        event_data = (
            event.event_data
            if isinstance(getattr(event, "event_data", None), dict)
            else {}
        )
        subscribe_id = self.__positive_int(event_data.get("subscribe_id"))
        if not subscribe_id:
            logger.warning("双重订阅联动取消：SubscribeDeleted 事件缺少 subscribe_id")
            return

        history_item = next(
            (
                item for item in self.__get_history()
                if int(item.get("subscribe_id") or 0) == subscribe_id
            ),
            None,
        )
        # 只处理曾由本插件记录的订阅，避免影响普通 MP 订阅。
        if not history_item:
            return
        self.__cancel_linked_subscription(
            subscribe_id=subscribe_id,
            history_item=history_item,
            origin="MP SubscribeDeleted 事件",
        )

    def __forward_record(
        self,
        subscribe: Any,
        trigger: str,
        resolved_tmdbid: Optional[int] = None,
    ) -> Dict[str, Any]:
        """将一条 TMDB 订阅发送到目标接口。"""
        subscribe_id = getattr(subscribe, "id", None)
        subscribe_data = subscribe.to_dict()
        payload = {
            key: value
            for key, value in subscribe_data.items()
            if key in self.API_WRITE_FIELDS and value is not None
        }
        tmdbid = resolved_tmdbid or self.__valid_tmdbid(subscribe)
        if not tmdbid:
            return self.__forward_result(False, "缺少有效 TMDB ID")
        payload["tmdbid"] = tmdbid
        payload["media_source"] = "themoviedb"
        payload["media_id"] = str(tmdbid)
        payload["mediaid"] = f"tmdb:{tmdbid}"
        for field in ("doubanid", "bangumiid", "anilistid"):
            payload.pop(field, None)

        access_token = self.__get_access_token()
        if not access_token:
            return self.__forward_result(False, "目标 MoviePilot 登录失败")

        headers = {
            "Accept": "application/json",
            **self._headers,
            "Authorization": f"Bearer {access_token}",
        }

        response = None
        try:
            response = requests.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            if response.status_code == 401:
                self._access_token = ""
                access_token = self.__get_access_token()
                if not access_token:
                    return self.__forward_result(False, "目标 MoviePilot 重新登录失败")
                headers["Authorization"] = f"Bearer {access_token}"
                response = requests.post(
                    self._endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self._timeout,
                )
            response.raise_for_status()

            result = self.__response_json(response)
            if isinstance(result, dict) and result.get("success") is False:
                error_log = self.__api_error_message(result, self.__response_detail(response))
                logger.error(
                    f"双重订阅转发失败：trigger={trigger}, subscribe_id={subscribe_id}, "
                    f"status={response.status_code}, response={self.__response_detail(response)}"
                )
                return self.__forward_result(False, error_log)
            target_subscribe_id = self.__target_subscribe_id(result)
            logger.info(
                f"双重订阅转发成功：trigger={trigger}, subscribe_id={subscribe_id}, "
                f"status={response.status_code}, name={payload.get('name') or '-'}, "
                f"tmdbid={tmdbid}, target_subscribe_id={target_subscribe_id or '-'}"
            )
            return self.__forward_result(
                True,
                target_subscribe_id=target_subscribe_id,
            )
        except requests.RequestException as err:
            error_response = getattr(err, "response", None)
            if error_response is None:
                error_response = response
            status_code = getattr(error_response, "status_code", None)
            target = urlsplit(self._endpoint).netloc or "<invalid>"
            logger.error(
                f"双重订阅转发失败：trigger={trigger}, subscribe_id={subscribe_id}, target={target}, "
                f"error={type(err).__name__}, status={status_code or '-'}, "
                f"response={self.__response_detail(error_response)}"
            )
            detail = self.__response_detail(error_response)
            error_log = f"目标接口请求失败（HTTP {status_code}）：{detail}" if status_code else (
                f"目标接口请求失败：{type(err).__name__}"
            )
            return self.__forward_result(False, error_log)
        except Exception as err:
            logger.exception(f"双重订阅转发发生未预期异常：{err}")
            return self.__forward_result(False, f"同步异常：{str(err) or type(err).__name__}")

    @staticmethod
    def __forward_result(
        success: bool,
        error_log: str = "",
        target_subscribe_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """生成统一的目标端同步结果。"""
        return {
            "success": bool(success),
            "error_log": str(error_log or ""),
            "target_subscribe_id": target_subscribe_id,
        }

    @classmethod
    def __target_subscribe_id(cls, result: Any) -> Optional[int]:
        """从 MoviePilot 新增订阅响应中提取目标端订阅 ID。"""
        if not isinstance(result, dict):
            return None
        data = result.get("data")
        if isinstance(data, dict):
            value = data.get("id") or data.get("subscribe_id")
        else:
            value = result.get("id") or result.get("subscribe_id")
        return cls.__positive_int(value) or None

    @staticmethod
    def __positive_int(value: Any) -> int:
        """将值转换为正整数，失败时返回零。"""
        try:
            number = int(value)
            return number if number > 0 else 0
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def __api_error_message(result: Any, fallback: str) -> str:
        """优先读取 MoviePilot API 返回的可读错误信息。"""
        if isinstance(result, dict):
            for key in ("message", "detail", "error"):
                if result.get(key):
                    return str(result[key])[:500]
        return str(fallback or "目标接口返回失败")[:500]

    def __unsubscribe_target(
        self,
        target_subscribe_id: int,
        source_subscribe_id: int,
    ) -> Tuple[bool, str]:
        """按目标订阅 ID 调用 MoviePilot 删除接口。"""
        delete_url = f"{self._endpoint.rstrip('/')}/{int(target_subscribe_id)}"
        return self.__delete_target_request(
            delete_url=delete_url,
            source_subscribe_id=source_subscribe_id,
            target_label=f"target_subscribe_id={target_subscribe_id}",
        )

    def __unsubscribe_target_media(
        self,
        history_item: Dict[str, Any],
        source_subscribe_id: int,
    ) -> Tuple[bool, str]:
        """目标响应无订阅 ID 时，按官方 TMDB 媒体键删除目标订阅。"""
        tmdbid = self.__positive_int(history_item.get("tmdbid"))
        if not tmdbid:
            return False, "历史记录缺少有效 TMDB ID"
        media_key = f"tmdb:{tmdbid}"
        delete_url = (
            f"{self._endpoint.rstrip('/')}/media/"
            f"{quote(media_key, safe='')}"
        )
        season = self.__positive_int(history_item.get("season"))
        if season:
            delete_url = f"{delete_url}?{urlencode({'season': season})}"
        return self.__delete_target_request(
            delete_url=delete_url,
            source_subscribe_id=source_subscribe_id,
            target_label=f"media={media_key}, season={season or '-'}",
        )

    def __delete_target_request(
        self,
        delete_url: str,
        source_subscribe_id: int,
        target_label: str,
    ) -> Tuple[bool, str]:
        """发送目标端删除请求，处理登录、401 重试和错误响应。"""
        access_token = self.__get_access_token()
        if not access_token:
            return False, "目标 MoviePilot 登录失败"

        headers = {
            "Accept": "application/json",
            **self._headers,
            "Authorization": f"Bearer {access_token}",
        }
        response = None
        try:
            response = requests.delete(
                delete_url,
                headers=headers,
                timeout=self._timeout,
            )
            if response.status_code == 401:
                self._access_token = ""
                access_token = self.__get_access_token()
                if not access_token:
                    return False, "目标 MoviePilot 重新登录失败"
                headers["Authorization"] = f"Bearer {access_token}"
                response = requests.delete(
                    delete_url,
                    headers=headers,
                    timeout=self._timeout,
                )
            response.raise_for_status()
            result = self.__response_json(response)
            if isinstance(result, dict) and result.get("success") is False:
                return False, self.__api_error_message(
                    result,
                    self.__response_detail(response),
                )
            logger.info(
                f"双重订阅取消：目标订阅已取消，subscribe_id={source_subscribe_id}, "
                f"{target_label}"
            )
            return True, ""
        except requests.RequestException as err:
            error_response = getattr(err, "response", None)
            if error_response is None:
                error_response = response
            status_code = getattr(error_response, "status_code", None)
            detail = self.__response_detail(error_response)
            return False, (
                f"HTTP {status_code}：{detail}" if status_code
                else f"{type(err).__name__}：{str(err) or detail}"
            )
        except Exception as err:
            logger.exception(
                f"双重订阅取消：目标端取消发生异常，subscribe_id={source_subscribe_id}, error={err}"
            )
            return False, str(err) or type(err).__name__

    def stop_service(self) -> None:
        """停止搜索钩子和内存调度器，持久化待恢复任务保持不变。"""
        self.__remove_search_hook()
        if self._scheduler:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception as err:
                logger.warning(f"双重订阅转发：停止延迟恢复调度器失败：{err}")
            finally:
                self._scheduler = None

    @staticmethod
    def __valid_tmdbid(subscribe: Any) -> int:
        """返回有效的 TMDB ID，不接受其它媒体来源的通用 ID。"""
        source = str(getattr(subscribe, "media_source", None) or "").strip().lower()
        if source and source not in {"tmdb", "themoviedb"}:
            return 0
        try:
            tmdbid = int(getattr(subscribe, "tmdbid", None))
            return tmdbid if tmdbid > 0 else 0
        except (TypeError, ValueError):
            return 0

    def __resolve_douban_tmdbid(self, subscribe: Any) -> Tuple[int, str]:
        """使用 MoviePilot 内部媒体识别链将豆瓣订阅匹配到 TMDB ID。"""
        doubanid = str(
            getattr(subscribe, "doubanid", None)
            or getattr(subscribe, "media_id", None)
            or getattr(subscribe, "mediaid", None)
            or ""
        ).strip()
        if doubanid.lower().startswith("douban:"):
            doubanid = doubanid.split(":", 1)[1].strip()
        if not doubanid:
            return 0, "订阅没有豆瓣 ID"
        title = str(getattr(subscribe, "name", None) or "").strip()
        if not title:
            return 0, f"豆瓣 ID={doubanid} 缺少标题，无法匹配 TMDB"
        try:
            from app.chain.media import MediaChain
            from app.core.metainfo import MetaInfo

            meta = MetaInfo(title)
            meta.year = str(getattr(subscribe, "year", None) or "") or None
            meta.type = (
                MediaType.TV
                if str(getattr(subscribe, "type", None) or "") == MediaType.TV.value
                else MediaType.MOVIE
            )
            meta.begin_season = getattr(subscribe, "season", None)
            mediainfo = MediaChain().recognize_by_meta(
                meta,
                source="themoviedb",
                obtain_images=False,
            )
            tmdbid = self.__positive_int(getattr(mediainfo, "tmdb_id", None))
            if not tmdbid:
                return 0, f"豆瓣 ID={doubanid} 未匹配到 TMDB ID"
            logger.info(
                f"双重订阅转发：豆瓣 ID 已转换为 TMDB ID，doubanid={doubanid}, "
                f"tmdbid={tmdbid}, title={title}"
            )
            return tmdbid, ""
        except Exception as err:
            logger.warning(
                f"双重订阅转发：豆瓣 ID 转换 TMDB ID 失败，doubanid={doubanid}, "
                f"error={type(err).__name__}: {err}"
            )
            return 0, f"豆瓣 ID 转换失败：{str(err) or type(err).__name__}"

    def __pause_local_subscription(self, subscribe: Any) -> Tuple[Optional[str], str]:
        """将本地新订阅暂停，并按用户设置登记恢复任务。"""
        subscribe_id = getattr(subscribe, "id", None)
        state = str(getattr(subscribe, "state", None) or "")
        if not subscribe_id:
            return None, "MP 本地暂停失败（缺少订阅 ID）"

        existing = self.__find_pending(int(subscribe_id))
        if state == "S" and existing:
            resume_at = existing.get("resume_at")
            return resume_at, f"MP 已暂停，预计 {self.__display_time(resume_at)} 恢复"
        if state != "N":
            return None, f"MP 本地未暂停（当前状态 {state or '-'}）"

        try:
            SubscribeOper().update(int(subscribe_id), {"state": "S"})
            resume_time = self.__now() + timedelta(minutes=self._pause_minutes)
            resume_at = resume_time.isoformat()
            pending = [
                item for item in self.__pending_entries()
                if int(item.get("subscribe_id") or 0) != int(subscribe_id)
            ]
            pending.append({
                "subscribe_id": int(subscribe_id),
                "resume_at": resume_at,
            })
            self.__save_pending(pending)
            self.__schedule_resume(int(subscribe_id), resume_time)
            logger.info(
                f"双重订阅转发：MP 本地订阅已暂停 {self._pause_minutes} 分钟，"
                f"subscribe_id={subscribe_id}, resume_at={self.__display_time(resume_at)}"
            )
            return resume_at, f"MP 已暂停，预计 {self.__display_time(resume_at)} 恢复"
        except Exception as err:
            logger.exception(f"双重订阅转发：暂停 MP 本地订阅失败：subscribe_id={subscribe_id}, error={err}")
            return None, "MP 本地暂停失败"

    def __resume_subscription(self, subscribe_id: int, reason: str = "等待时间已到") -> None:
        """恢复前检查 Emby，完整入库则删除本地订阅，否则恢复订阅。"""
        local_status = "MP 恢复检查完成"
        try:
            subscribe = SubscribeOper().get(int(subscribe_id))
            if not subscribe:
                local_status = "MP 订阅已不存在"
            elif str(getattr(subscribe, "state", None) or "") == "S":
                emby_complete, emby_error = self.__emby_has_complete_subscription(subscribe)
                if emby_complete:
                    SubscribeOper().delete(int(subscribe_id))
                    local_status = "Emby 已完整入库，MP 暂停订阅已取消"
                    self.__cancel_linked_subscription(
                        subscribe_id=int(subscribe_id),
                        origin="Emby 完整入库",
                    )
                    logger.info(
                        f"双重订阅转发：Emby 已完整入库，已取消 MP 本地订阅，"
                        f"subscribe_id={subscribe_id}, reason={reason}"
                    )
                else:
                    SubscribeOper().update(int(subscribe_id), {"state": "R"})
                    local_status = (
                        "Emby 检查异常，MP 已恢复为订阅中"
                        if emby_error else "MP 已恢复为订阅中"
                    )
                    logger.info(
                        f"双重订阅转发：MP 本地订阅已恢复，"
                        f"subscribe_id={subscribe_id}, reason={reason}"
                    )
            else:
                state = str(getattr(subscribe, "state", None) or "-")
                local_status = f"MP 已由用户调整（当前状态 {state}）"
                logger.info(
                    f"双重订阅转发：跳过自动恢复，subscribe_id={subscribe_id}, state={state}"
                )
        except Exception as err:
            local_status = "MP 自动恢复失败，稍后重试"
            logger.exception(
                f"双重订阅转发：恢复 MP 本地订阅失败：subscribe_id={subscribe_id}, error={err}"
            )
            self.__schedule_resume(
                int(subscribe_id), self.__now() + timedelta(minutes=1)
            )
            return

        pending = [
            item for item in self.__pending_entries()
            if int(item.get("subscribe_id") or 0) != int(subscribe_id)
        ]
        self.__save_pending(pending)
        self.__update_history_local_status(int(subscribe_id), local_status)

    @staticmethod
    def __emby_has_complete_subscription(subscribe: Any) -> Tuple[bool, bool]:
        """检查任一已启用 Emby 是否已完整包含当前电影或电视剧订阅范围。"""
        try:
            services = MediaServerHelper().get_services(type_filter="emby")
        except Exception as err:
            logger.warning(f"双重订阅转发：读取 Emby 服务失败：{err}")
            return False, True
        if not services:
            return False, False

        media_type = (
            MediaType.TV
            if str(getattr(subscribe, "type", None) or "") == MediaType.TV.value
            else MediaType.MOVIE
        )
        mediainfo = MediaInfo(
            source="themoviedb",
            media_id=str(getattr(subscribe, "tmdbid", None) or ""),
            type=media_type,
            title=getattr(subscribe, "name", None),
            year=str(getattr(subscribe, "year", None) or "") or None,
            season=getattr(subscribe, "season", None),
            tmdb_id=getattr(subscribe, "tmdbid", None),
        )
        season = int(getattr(subscribe, "season", None) or 1)
        start_episode = int(getattr(subscribe, "start_episode", None) or 1)
        total_episode = int(getattr(subscribe, "total_episode", None) or 0)
        target_episodes = (
            set(range(start_episode, total_episode + 1))
            if media_type == MediaType.TV and total_episode >= start_episode
            else set()
        )
        if media_type == MediaType.TV and not target_episodes:
            logger.info(
                f"双重订阅转发：订阅 {getattr(subscribe, 'id', '-')} 缺少有效总集数，"
                "不判定 Emby 已完整入库"
            )
            return False, False

        check_error = False
        media_chain = MediaServerChain()
        for server_name in services:
            try:
                exists = media_chain.media_exists(mediainfo=mediainfo, server=server_name)
            except Exception as err:
                check_error = True
                logger.warning(
                    f"双重订阅转发：查询 Emby 媒体库失败：server={server_name}, error={err}"
                )
                continue
            if not exists or str(getattr(exists, "server_type", "") or "").lower() != "emby":
                continue
            if media_type == MediaType.MOVIE:
                return True, check_error
            seasons = getattr(exists, "seasons", None) or {}
            existing_episodes = seasons.get(season) or seasons.get(str(season)) or []
            try:
                existing_episode_numbers = {int(value) for value in existing_episodes}
            except (TypeError, ValueError) as err:
                check_error = True
                logger.warning(
                    f"双重订阅转发：Emby 剧集数据格式异常：server={server_name}, error={err}"
                )
                continue
            if target_episodes.issubset(existing_episode_numbers):
                return True, check_error
        return False, check_error

    def __start_resume_scheduler(self) -> None:
        """启动本插件专用的延迟恢复调度器。"""
        if self._scheduler:
            return
        self._scheduler = BackgroundScheduler(timezone=settings.TZ)
        self._scheduler.start()

    def __schedule_resume(self, subscribe_id: int, run_date: datetime) -> None:
        """注册或替换一条订阅恢复任务。"""
        if not self._enabled:
            return
        self.__start_resume_scheduler()
        self._scheduler.add_job(
            func=self.__resume_subscription,
            trigger="date",
            run_date=run_date,
            args=[int(subscribe_id)],
            id=f"dualsubscribe_resume_{subscribe_id}",
            name=f"双重订阅恢复 {subscribe_id}",
            replace_existing=True,
            misfire_grace_time=3600,
        )

    def __restore_pending_resumes(self) -> None:
        """插件加载时恢复尚未执行的延迟任务。"""
        now = self.__now()
        for item in list(self.__pending_entries()):
            subscribe_id = int(item.get("subscribe_id") or 0)
            resume_time = self.__parse_time(item.get("resume_at"))
            if not subscribe_id or not resume_time or resume_time <= now:
                if subscribe_id:
                    self.__resume_subscription(subscribe_id, reason="MoviePilot 重启后补偿恢复")
                continue
            self.__schedule_resume(subscribe_id, resume_time)
        if self.__pending_entries():
            logger.info(
                f"双重订阅转发：已恢复 {len(self.__pending_entries())} 条延迟恢复任务"
            )

    def __resume_all_pending(self, reason: str) -> None:
        """插件停用时立即恢复由插件暂停的全部订阅。"""
        for item in list(self.__pending_entries()):
            subscribe_id = int(item.get("subscribe_id") or 0)
            if subscribe_id:
                self.__resume_subscription(subscribe_id, reason=reason)

    def __save_subscribe_history(
        self,
        subscribe: Any,
        target_status: str,
        local_status: str,
        resume_at: Optional[str] = None,
        error_log: Optional[str] = None,
        target_subscribe_id: Optional[int] = None,
        resolved_tmdbid: Optional[int] = None,
    ) -> None:
        """新增或更新订阅历史，供插件详情页展示海报墙。"""
        try:
            subscribe_id = getattr(subscribe, "id", None)
            entry = {
                "subscribe_id": getattr(subscribe, "id", None),
                "title": getattr(subscribe, "name", None),
                "year": getattr(subscribe, "year", None),
                "type": getattr(subscribe, "type", None),
                "season": getattr(subscribe, "season", None),
                "tmdbid": resolved_tmdbid or self.__valid_tmdbid(subscribe) or None,
                "poster": getattr(subscribe, "poster", None),
                "backdrop": getattr(subscribe, "backdrop", None),
                "vote": getattr(subscribe, "vote", None),
                "description": getattr(subscribe, "description", None),
                "target_status": target_status,
                "local_status": local_status,
                "resume_at": resume_at,
                "time": getattr(subscribe, "date", None)
                        or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            if error_log is not None:
                entry["error_log"] = str(error_log)
            if target_subscribe_id is not None:
                entry["target_subscribe_id"] = int(target_subscribe_id)
            with self._data_lock:
                history = self.__get_history()
                old_entry = next(
                    (item for item in history if item.get("subscribe_id") == subscribe_id),
                    None,
                )
                if old_entry:
                    old_entry.update(entry)
                else:
                    history.append(entry)
                self.save_data(self.HISTORY_KEY, history)
        except Exception as err:
            logger.warning(f"双重订阅转发：保存订阅海报历史失败：{err}")

    def __get_history(self) -> List[Dict[str, Any]]:
        """读取历史列表，并兼容迁移 1.3.0 的单条历史数据。"""
        history = self.get_data(self.HISTORY_KEY) or []
        if not isinstance(history, list):
            history = []
        if not history:
            latest = self.get_data("latest_subscribe") or {}
            if isinstance(latest, dict) and latest:
                migrated = dict(latest)
                migrated["target_status"] = migrated.pop("status", "历史记录")
                migrated.setdefault("local_status", "升级前状态未知")
                history = [migrated]
                self.save_data(self.HISTORY_KEY, history)
        return [item for item in history if isinstance(item, dict)]

    def __update_history_local_status(self, subscribe_id: int, status: str) -> None:
        """更新指定历史记录的 MoviePilot 本地状态。"""
        with self._data_lock:
            history = self.__get_history()
            for item in history:
                if int(item.get("subscribe_id") or 0) == int(subscribe_id):
                    item["local_status"] = status
                    item["resume_at"] = None
                    break
            self.save_data(self.HISTORY_KEY, history)

    def __pending_entries(self) -> List[Dict[str, Any]]:
        """读取格式有效的待恢复任务列表。"""
        pending = self.get_data(self.PENDING_KEY) or []
        if not isinstance(pending, list):
            return []
        return [item for item in pending if isinstance(item, dict)]

    def __save_pending(self, pending: List[Dict[str, Any]]) -> None:
        """持久化待恢复任务列表。"""
        with self._data_lock:
            self.save_data(self.PENDING_KEY, pending)

    def __find_pending(self, subscribe_id: int) -> Optional[Dict[str, Any]]:
        """按订阅 ID 查询待恢复任务。"""
        return next(
            (
                item for item in self.__pending_entries()
                if int(item.get("subscribe_id") or 0) == int(subscribe_id)
            ),
            None,
        )

    def __remove_pending_resume(self, subscribe_id: int) -> None:
        """删除指定订阅的持久化恢复任务和内存调度任务。"""
        pending = [
            item for item in self.__pending_entries()
            if int(item.get("subscribe_id") or 0) != int(subscribe_id)
        ]
        self.__save_pending(pending)
        if not self._scheduler:
            return
        try:
            self._scheduler.remove_job(f"dualsubscribe_resume_{int(subscribe_id)}")
        except Exception:
            # 任务可能已执行、未注册，或测试调度器没有 remove_job；均无需阻断删除。
            pass

    @staticmethod
    def __media_subtitle(item: Dict[str, Any]) -> str:
        """生成海报卡片的媒体摘要。"""
        parts = [str(item.get("type") or "未知类型")]
        if item.get("year"):
            parts.append(str(item.get("year")))
        if item.get("season"):
            parts.append(f"第 {item.get('season')} 季")
        if item.get("vote"):
            parts.append(f"{item.get('vote')} 分")
        return " · ".join(parts)

    @staticmethod
    def __detail_line(icon: str, value: str) -> Dict[str, Any]:
        """生成横向媒体卡片中的一行图标与文字。"""
        return {
            "component": "div",
            "props": {
                "class": "d-flex align-center text-caption text-medium-emphasis mb-1",
                "title": value,
            },
            "content": [{
                "component": "VIcon",
                "props": {"icon": icon, "size": 14, "class": "me-1 flex-shrink-0"},
            }, {
                "component": "span",
                "props": {"class": "text-truncate"},
                "text": value,
            }],
        }

    @staticmethod
    def __status_badge(item: Dict[str, Any]) -> Tuple[str, str, str]:
        """根据目标端和本地状态生成海报角标。"""
        target_status = str(item.get("target_status") or "")
        local_status = str(item.get("local_status") or "")
        if "失败" in target_status:
            return "同步失败", "error", "mdi-cloud-alert-outline"
        if "暂停" in local_status:
            return "暂停中", "warning", "mdi-pause-circle-outline"
        if "恢复" in local_status or "未暂停" in local_status:
            return "订阅中", "success", "mdi-bell-ring-outline"
        if "用户调整" in local_status:
            return "已调整", "primary", "mdi-account-edit-outline"
        return "已记录", "info", "mdi-check-circle-outline"

    @staticmethod
    def __category_value(item: Dict[str, Any]) -> str:
        """将媒体类型转换为极简列表使用的分类文本。"""
        media_type = str(item.get("type") or "电影")
        return f"类型{media_type}"

    @classmethod
    def __minute_time(cls, value: Any) -> str:
        """将订阅时间统一格式化到分钟。"""
        parsed = cls.__parse_time(value)
        if parsed:
            return parsed.strftime("%Y-%m-%d %H:%M")
        return str(value or "-")[:16]

    @staticmethod
    def __release_year(value: Any) -> int:
        """将发行年份归一为四位纯数字，无有效年份时返回零。"""
        digits = "".join(char for char in str(value or "") if char.isdigit())
        return int(digits[:4]) if len(digits) >= 4 else 0

    @staticmethod
    def __status_value(item: Dict[str, Any]) -> str:
        """将内部处理状态严格映射为四种页面枚举值。"""
        target_status = str(item.get("target_status") or "")
        local_status = str(item.get("local_status") or "")
        if not item.get("tmdbid") or "跳过" in target_status or "缺少" in target_status:
            return "未识别"
        if any(word in f"{target_status}{local_status}" for word in ("失败", "异常")):
            return "异常"
        if "暂停" in local_status and "取消" not in local_status:
            return "已暂停"
        if "成功" in target_status:
            return "双重订阅"
        return "异常"

    @staticmethod
    def __error_log_value(item: Dict[str, Any], status: str) -> str:
        """仅为异常和未识别状态返回可读日志。"""
        if status not in {"异常", "未识别"}:
            return ""
        error_log = str(item.get("error_log") or "").strip()
        if error_log:
            return error_log
        if status == "未识别":
            return "缺少有效 TMDB ID，目标接口仅支持 TMDB ID"
        target_status = str(item.get("target_status") or "目标端同步异常")
        local_status = str(item.get("local_status") or "")
        return "；".join(value for value in (target_status, local_status) if value)

    @staticmethod
    def __now() -> datetime:
        """返回 MoviePilot 配置时区下的当前时间。"""
        return datetime.now(tz=ZoneInfo(settings.TZ))

    @classmethod
    def __parse_time(cls, value: Any) -> Optional[datetime]:
        """解析持久化的 ISO 时间，并补齐 MoviePilot 时区。"""
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo(settings.TZ))
            return parsed
        except (TypeError, ValueError):
            return None

    @classmethod
    def __display_time(cls, value: Any) -> str:
        """将 ISO 时间格式化为页面和日志使用的本地时间。"""
        parsed = cls.__parse_time(value)
        return parsed.strftime("%Y-%m-%d %H:%M:%S") if parsed else "未知时间"

    def __sync_before_auto_search(self, state: str):
        """在 MoviePilot 自动搜索前同步对应状态的全部 TMDB 订阅。"""
        try:
            subscribes = SubscribeOper().list(state=state) or []
        except Exception as err:
            logger.exception(f"双重订阅转发：读取自动搜索订阅失败：state={state}, error={err}")
            return

        candidates = [
            subscribe for subscribe in subscribes
            if self.__valid_tmdbid(subscribe)
            or str(getattr(subscribe, "doubanid", None) or "").strip()
        ]
        logger.info(
            f"双重订阅转发：自动搜索前开始同步，state={state}, "
            f"total={len(subscribes)}, tmdb={len(candidates)}"
        )
        success_count = 0
        for subscribe in candidates:
            resolved_tmdbid = self.__valid_tmdbid(subscribe)
            if not resolved_tmdbid:
                resolved_tmdbid, _ = self.__resolve_douban_tmdbid(subscribe)
            result = self.__forward_record(
                subscribe,
                trigger=f"自动搜索前({state})",
                resolved_tmdbid=resolved_tmdbid or None,
            )
            if result["success"]:
                success_count += 1
        logger.info(
            f"双重订阅转发：自动搜索前同步完成，state={state}, "
            f"success={success_count}, failed={len(candidates) - success_count}, "
            f"skipped={len(subscribes) - len(candidates)}"
        )

    def __configure_search_hook(self):
        """按配置安装或移除 MoviePilot 订阅搜索前置钩子。"""
        self.__remove_search_hook()
        if not self._enabled or not self._sync_before_auto_search:
            return

        from app.chain.subscribe import SubscribeChain

        original = SubscribeChain.search
        plugin = self

        def search_wrapper(
            chain_self,
            sid=None,
            state="N",
            manual=False,
            progress_callback=None,
        ):
            """在系统自动订阅搜索前执行目标端同步。"""
            if not manual and sid is None and state in {"N", "R"}:
                plugin.__sync_before_auto_search(state)
            return original(
                chain_self,
                sid=sid,
                state=state,
                manual=manual,
                progress_callback=progress_callback,
            )

        setattr(search_wrapper, "_dualsubscribe_original", original)
        SubscribeChain.search = search_wrapper
        self.__rewire_existing_scheduler(search_wrapper)
        logger.info("双重订阅转发：已启用 MoviePilot 自动订阅搜索前置同步")

    def __remove_search_hook(self):
        """恢复 MoviePilot 原始订阅搜索方法。"""
        try:
            from app.chain.subscribe import SubscribeChain

            current = SubscribeChain.search
            original = getattr(current, "_dualsubscribe_original", None)
            if not original:
                return
            SubscribeChain.search = original
            self.__rewire_existing_scheduler(original)
        except Exception as err:
            logger.warning(f"双重订阅转发：移除自动搜索前置钩子失败：{err}")

    @staticmethod
    def __rewire_existing_scheduler(search_method):
        """插件热更新时同步替换已创建的系统定时任务函数。"""
        try:
            from app.scheduler import Scheduler

            scheduler = Scheduler.get_existing_instance()
            if not scheduler:
                return
            for job_id in ("new_subscribe_search", "subscribe_search"):
                job = scheduler._jobs.get(job_id)  # noqa: SLF001
                if not job or not job.get("func"):
                    continue
                chain_instance = getattr(job["func"], "__self__", None)
                if chain_instance:
                    job["func"] = search_method.__get__(
                        chain_instance, chain_instance.__class__
                    )
        except Exception as err:
            logger.warning(f"双重订阅转发：更新系统订阅搜索任务失败：{err}")

    @staticmethod
    def __safe_timeout(value: Any) -> int:
        """将请求超时限制在 1 到 60 秒之间。"""
        try:
            timeout = int(value)
        except (TypeError, ValueError):
            timeout = 10
        return max(1, min(timeout, 60))

    @classmethod
    def __safe_pause_minutes(cls, value: Any) -> int:
        """将本地暂停时间限制在 1 分钟到 7 天之间。"""
        try:
            minutes = int(value)
        except (TypeError, ValueError):
            minutes = cls.DEFAULT_PAUSE_MINUTES
        return max(1, min(minutes, 10080))

    @classmethod
    def __normalize_endpoint(cls, endpoint: str) -> str:
        """兼容旧版保存的令牌基础地址，自动补全 MoviePilot 新增订阅路由。"""
        if endpoint.rstrip("/") == cls.ENDPOINT_BASE.rstrip("/"):
            return f"{endpoint.rstrip('/')}/api/v1/subscribe/"
        return endpoint

    def __get_access_token(self) -> str:
        """登录目标 MoviePilot 并缓存访问令牌。"""
        if self._access_token:
            return self._access_token
        if not self._username or not self._password:
            logger.error("双重订阅转发登录失败：目标用户名或密码未配置")
            return ""

        login_url = self.__login_url()
        target = urlsplit(login_url).netloc or "<invalid>"
        response = None
        try:
            response = requests.post(
                login_url,
                data={"username": self._username, "password": self._password},
                headers={"Accept": "application/json"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            result = self.__response_json(response)
            access_token = result.get("access_token") if isinstance(result, dict) else None
            if not access_token:
                logger.error(
                    f"双重订阅转发登录失败：target={target}, status={response.status_code}, "
                    f"response={self.__response_detail(response)}"
                )
                return ""
            self._access_token = str(access_token)
            logger.info(f"双重订阅转发：目标 MoviePilot 登录成功，target={target}")
            return self._access_token
        except requests.RequestException as err:
            error_response = getattr(err, "response", None)
            if error_response is None:
                error_response = response
            logger.error(
                f"双重订阅转发登录失败：target={target}, error={type(err).__name__}, "
                f"status={getattr(error_response, 'status_code', None) or '-'}, "
                f"response={self.__response_detail(error_response)}"
            )
            return ""

    def __login_url(self) -> str:
        """从订阅接口 URL 推导同一前缀下的登录接口 URL。"""
        parsed = urlsplit(self._endpoint)
        marker = "/api/v1/"
        marker_index = parsed.path.find(marker)
        if marker_index >= 0:
            prefix = parsed.path[:marker_index]
        else:
            prefix = parsed.path.rstrip("/")
        login_path = f"{prefix}/api/v1/login/access-token"
        return urlunsplit((parsed.scheme, parsed.netloc, login_path, "", ""))

    @staticmethod
    def __parse_headers(value: Any) -> Dict[str, str]:
        """解析用户配置的额外 HTTP 请求头。"""
        if not value:
            return {}
        if isinstance(value, dict):
            data = value
        else:
            try:
                data = json.loads(str(value))
            except (TypeError, ValueError, json.JSONDecodeError) as err:
                logger.error(f"双重订阅转发：额外请求头不是合法 JSON，将忽略：{err}")
                return {}
        if not isinstance(data, dict):
            logger.error("双重订阅转发：额外请求头必须是 JSON 对象，将忽略")
            return {}
        return {str(key): str(val) for key, val in data.items()}

    @staticmethod
    def __response_json(response: requests.Response) -> Any:
        """尽可能将 HTTP 响应解析为 JSON。"""
        if response is None:
            return None
        try:
            return response.json()
        except (TypeError, ValueError):
            return None

    @classmethod
    def __response_detail(cls, response: requests.Response) -> str:
        """返回截断后的目标响应，避免错误页淹没日志。"""
        if response is None:
            return "-"
        data = cls.__response_json(response)
        if data is not None:
            detail = json.dumps(data, ensure_ascii=False, default=str)
        else:
            detail = (getattr(response, "text", "") or "").strip()
        detail = " ".join(detail.split())
        return detail[:500] or "-"
