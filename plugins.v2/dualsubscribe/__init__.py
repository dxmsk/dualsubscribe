import json
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urlsplit, urlunsplit

import requests

from app.core.event import eventmanager
from app.db.subscribe_oper import SubscribeOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType


class DualSubscribe(_PluginBase):
    """将 MoviePilot 新增订阅同步到兼容 MoviePilot API 的外部接口。"""

    plugin_name = "双重订阅转发"
    plugin_desc = "MoviePilot 新增订阅时，将完整订阅参数同步到兼容接口。"
    plugin_icon = "dualsubscribe.svg"
    plugin_version = "1.3.0"
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
    _username = "admin"
    _password = "admin"
    _access_token = ""
    _sync_before_auto_search = False
    _headers: Dict[str, str] = {}

    def init_plugin(self, config: dict = None):
        config = config or {}
        self._enabled = bool(config.get("enabled", False))
        self._endpoint = self.__normalize_endpoint(
            str(config.get("endpoint") or self.DEFAULT_ENDPOINT).strip()
        )
        self._timeout = self.__safe_timeout(config.get("timeout", 10))
        self._username = str(config.get("username") or "admin").strip()
        self._password = str(config.get("password") or "admin")
        self._access_token = ""
        self._sync_before_auto_search = bool(config.get("sync_before_auto_search", False))
        self._headers = self.__parse_headers(config.get("headers"))
        self.__configure_search_hook()

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
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
                                "props": {"cols": 12, "md": 4},
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
                                "props": {"cols": 12, "md": 4},
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
                                "仅同步带有效 TMDB ID 的订阅。开启“自动搜索前再次同步”后，"
                                "MoviePilot 的自动订阅搜索会等待接口同步完成后再开始。"
                            ),
                        },
                    },
                ],
            }
        ], {
            "enabled": False,
            "endpoint": self.DEFAULT_ENDPOINT,
            "timeout": 10,
            "username": "admin",
            "password": "admin",
            "sync_before_auto_search": False,
            "headers": "",
        }

    def get_page(self) -> List[dict]:
        latest = self.get_data("latest_subscribe") or {}
        if not latest:
            return [{
                "component": "VAlert",
                "props": {
                    "type": "info",
                    "variant": "tonal",
                    "text": "暂无新增订阅记录",
                },
            }]

        poster = latest.get("poster")
        tmdbid = latest.get("tmdbid")
        media_path = "tv" if latest.get("type") == "电视剧" else "movie"
        info_content = [
            {
                "component": "VCardTitle",
                "props": {"class": "text-h6 pb-1"},
                "text": latest.get("title") or "未知标题",
            },
            {
                "component": "VCardText",
                "props": {"class": "py-1"},
                "text": f"TMDB ID：{tmdbid or '-'}",
            },
            {
                "component": "VCardText",
                "props": {"class": "py-1"},
                "text": f"类型：{latest.get('type') or '-'}  季：{latest.get('season') or '-'}",
            },
            {
                "component": "VCardText",
                "props": {"class": "py-1"},
                "text": f"同步状态：{latest.get('status') or '-'}",
            },
            {
                "component": "VCardText",
                "props": {"class": "py-1"},
                "text": f"添加时间：{latest.get('time') or '-'}",
            },
        ]
        if tmdbid:
            info_content.append({
                "component": "VBtn",
                "props": {
                    "class": "ma-2",
                    "variant": "tonal",
                    "href": f"https://www.themoviedb.org/{media_path}/{tmdbid}",
                    "target": "_blank",
                },
                "text": "查看 TMDB",
            })

        row_content = []
        if poster:
            row_content.append({
                "component": "VImg",
                "props": {
                    "src": poster,
                    "width": 180,
                    "height": 270,
                    "aspect-ratio": "2/3",
                    "cover": True,
                    "class": "rounded ma-4 flex-shrink-0",
                },
            })
        row_content.append({
            "component": "div",
            "props": {"class": "pa-3 flex-grow-1"},
            "content": info_content,
        })
        return [{
            "component": "VCard",
            "props": {"variant": "tonal"},
            "content": [{
                "component": "div",
                "props": {"class": "d-flex flex-wrap align-center"},
                "content": row_content,
            }],
        }]

    @eventmanager.register(EventType.SubscribeAdded)
    def forward_subscription(self, event):
        """读取刚创建的订阅，并按 MoviePilot 新增订阅 API 格式转发。"""
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
        self.__save_latest_subscribe(
            subscribe,
            "等待同步" if tmdbid else "已跳过（缺少 TMDB ID）",
        )
        if not tmdbid:
            logger.warning(
                f"双重订阅转发跳过：subscribe_id={subscribe_id}, "
                f"name={getattr(subscribe, 'name', '-')}, 原因=目标接口仅支持 TMDB ID"
            )
            return

        success = self.__forward_record(subscribe, trigger="新增订阅")
        self.__save_latest_subscribe(subscribe, "同步成功" if success else "同步失败")

    def __forward_record(self, subscribe: Any, trigger: str) -> bool:
        """将一条 TMDB 订阅发送到目标接口。"""
        subscribe_id = getattr(subscribe, "id", None)
        subscribe_data = subscribe.to_dict()
        payload = {
            key: value
            for key, value in subscribe_data.items()
            if key in self.API_WRITE_FIELDS and value is not None
        }
        tmdbid = self.__valid_tmdbid(subscribe)
        if not tmdbid:
            return False
        payload["tmdbid"] = tmdbid
        payload["media_source"] = "themoviedb"
        payload["media_id"] = str(tmdbid)
        payload["mediaid"] = f"tmdb:{tmdbid}"
        for field in ("doubanid", "bangumiid", "anilistid"):
            payload.pop(field, None)

        access_token = self.__get_access_token()
        if not access_token:
            return False

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
                    return False
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
                logger.error(
                    f"双重订阅转发失败：trigger={trigger}, subscribe_id={subscribe_id}, "
                    f"status={response.status_code}, response={self.__response_detail(response)}"
                )
                return False
            logger.info(
                f"双重订阅转发成功：trigger={trigger}, subscribe_id={subscribe_id}, "
                f"status={response.status_code}, name={payload.get('name') or '-'}, "
                f"tmdbid={tmdbid}"
            )
            return True
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
            return False
        except Exception as err:
            logger.exception(f"双重订阅转发发生未预期异常：{err}")
            return False

    def stop_service(self):
        self.__remove_search_hook()

    @staticmethod
    def __valid_tmdbid(subscribe: Any) -> int:
        source = str(getattr(subscribe, "media_source", None) or "").strip().lower()
        if source and source not in {"tmdb", "themoviedb"}:
            return 0
        try:
            tmdbid = int(getattr(subscribe, "tmdbid", None))
            return tmdbid if tmdbid > 0 else 0
        except (TypeError, ValueError):
            return 0

    def __save_latest_subscribe(self, subscribe: Any, status: str):
        """保存最近新增订阅，供插件详情页展示。"""
        try:
            self.save_data("latest_subscribe", {
                "subscribe_id": getattr(subscribe, "id", None),
                "title": getattr(subscribe, "name", None),
                "year": getattr(subscribe, "year", None),
                "type": getattr(subscribe, "type", None),
                "season": getattr(subscribe, "season", None),
                "tmdbid": self.__valid_tmdbid(subscribe) or None,
                "poster": getattr(subscribe, "poster", None),
                "status": status,
                "time": getattr(subscribe, "date", None)
                        or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        except Exception as err:
            logger.warning(f"双重订阅转发：保存最近订阅详情失败：{err}")

    def __sync_before_auto_search(self, state: str):
        """在 MoviePilot 自动搜索前同步对应状态的全部 TMDB 订阅。"""
        try:
            subscribes = SubscribeOper().list(state=state) or []
        except Exception as err:
            logger.exception(f"双重订阅转发：读取自动搜索订阅失败：state={state}, error={err}")
            return

        candidates = [subscribe for subscribe in subscribes if self.__valid_tmdbid(subscribe)]
        logger.info(
            f"双重订阅转发：自动搜索前开始同步，state={state}, "
            f"total={len(subscribes)}, tmdb={len(candidates)}"
        )
        success_count = 0
        for subscribe in candidates:
            if self.__forward_record(subscribe, trigger=f"自动搜索前({state})"):
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
        try:
            timeout = int(value)
        except (TypeError, ValueError):
            timeout = 10
        return max(1, min(timeout, 60))

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
