import json
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
    plugin_version = "1.2.1"
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
        self._headers = self.__parse_headers(config.get("headers"))

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
                                "props": {"cols": 12, "md": 6},
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
                                "props": {"cols": 12, "md": 6},
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
                                "插件会先登录目标 MoviePilot，再发送完整订阅的 API 兼容请求。"
                                "401 时会重新登录并重试一次；其它失败不会撤销本地订阅。"
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
            "headers": "",
        }

    def get_page(self) -> List[dict]:
        return []

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

        subscribe_data = subscribe.to_dict()
        payload = {
            key: value
            for key, value in subscribe_data.items()
            if key in self.API_WRITE_FIELDS and value is not None
        }
        self.__normalize_media_identity(payload)

        access_token = self.__get_access_token()
        if not access_token:
            return

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
                    return
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
                    f"双重订阅转发失败：subscribe_id={subscribe_id}, "
                    f"status={response.status_code}, response={self.__response_detail(response)}"
                )
                return
            logger.info(
                f"双重订阅转发成功：subscribe_id={subscribe_id}, "
                f"status={response.status_code}, name={payload.get('name') or '-'}, "
                f"media={payload.get('media_source') or 'unknown'}:{payload.get('media_id') or '-'}"
            )
        except requests.RequestException as err:
            error_response = getattr(err, "response", None)
            if error_response is None:
                error_response = response
            status_code = getattr(error_response, "status_code", None)
            target = urlsplit(self._endpoint).netloc or "<invalid>"
            logger.error(
                f"双重订阅转发失败：subscribe_id={subscribe_id}, target={target}, "
                f"error={type(err).__name__}, status={status_code or '-'}, "
                f"response={self.__response_detail(error_response)}"
            )
        except Exception as err:
            logger.exception(f"双重订阅转发发生未预期异常：{err}")

    def stop_service(self):
        pass

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
    def __normalize_media_identity(payload: dict):
        """修正非 TMDB 来源被误写进 tmdbid 的情况，并补齐来源专用 ID。"""
        aliases = {"tmdb": "themoviedb"}
        source = str(payload.get("media_source") or "").strip().lower()
        source = aliases.get(source, source)
        media_id = payload.get("media_id")
        if not source or media_id in (None, ""):
            return

        source_fields = {
            "themoviedb": "tmdbid",
            "douban": "doubanid",
            "bangumi": "bangumiid",
            "anilist": "anilistid",
        }
        source_field = source_fields.get(source)
        if source_field and payload.get(source_field) in (None, ""):
            if source_field in {"tmdbid", "bangumiid", "anilistid"}:
                try:
                    payload[source_field] = int(media_id)
                except (TypeError, ValueError):
                    payload[source_field] = media_id
            else:
                payload[source_field] = str(media_id)

        if source != "themoviedb" and str(payload.get("tmdbid") or "") == str(media_id):
            payload.pop("tmdbid", None)

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
