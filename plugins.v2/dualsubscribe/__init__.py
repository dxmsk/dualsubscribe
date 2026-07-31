import json
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Tuple
from urllib.parse import urlsplit

import requests

from app.core.event import eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType


class DualSubscribe(_PluginBase):
    """将 MoviePilot 新增订阅事件同步转发到外部接口。"""

    plugin_name = "双重订阅转发"
    plugin_desc = "MoviePilot 新增订阅时，将订阅事件同步转发到指定接口。"
    plugin_icon = "dualsubscribe.svg"
    plugin_version = "1.0.0"
    plugin_author = "Codex"
    author_url = ""
    plugin_config_prefix = "dualsubscribe_"
    plugin_order = 30
    auth_level = 1

    DEFAULT_ENDPOINT = (
        "http://192.168.1.6:29999/mp/"
        "f1a20bf6399b1d0c1e32b5206eaf6ee63821d69dee5cf73d84cf6612b969eb7e"
    )

    _enabled = False
    _endpoint = DEFAULT_ENDPOINT
    _timeout = 10
    _payload_mode = "webhook"
    _headers: Dict[str, str] = {}

    def init_plugin(self, config: dict = None):
        config = config or {}
        self._enabled = bool(config.get("enabled", False))
        self._endpoint = str(config.get("endpoint") or self.DEFAULT_ENDPOINT).strip()
        self._timeout = self.__safe_timeout(config.get("timeout", 10))
        self._payload_mode = str(config.get("payload_mode") or "webhook").strip()
        if self._payload_mode not in {"webhook", "data"}:
            self._payload_mode = "webhook"
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
                                        "component": "VSelect",
                                        "props": {
                                            "model": "payload_mode",
                                            "label": "请求体格式",
                                            "items": [
                                                {
                                                    "title": "Webhook（type + data）",
                                                    "value": "webhook",
                                                },
                                                {
                                                    "title": "仅订阅数据（data）",
                                                    "value": "data",
                                                },
                                            ],
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
                                            "label": "外部订阅接口",
                                            "placeholder": "http://host/path",
                                            "hint": "新增订阅时向该地址发送一次 POST JSON 请求",
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
                                "插件只监听新增订阅事件。外部接口失败时会写入 MoviePilot 日志，"
                                "但不会撤销 MoviePilot 已添加的订阅，也不会自动重试。"
                            ),
                        },
                    },
                ],
            }
        ], {
            "enabled": False,
            "endpoint": self.DEFAULT_ENDPOINT,
            "timeout": 10,
            "payload_mode": "webhook",
            "headers": "",
        }

    def get_page(self) -> List[dict]:
        return []

    @eventmanager.register(EventType.SubscribeAdded)
    def forward_subscription(self, event):
        """处理订阅新增事件并转发。"""
        if not self._enabled or not self._endpoint:
            return
        if not event:
            return

        event_data = self.__to_json_value(event.event_data)
        if self._payload_mode == "data":
            payload = event_data
        else:
            payload = {
                "type": EventType.SubscribeAdded.value,
                "data": event_data,
            }

        headers = {
            "Accept": "application/json",
            "X-MoviePilot-Event": EventType.SubscribeAdded.value,
            **self._headers,
        }

        try:
            response = requests.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            logger.info(
                f"双重订阅转发成功：event={EventType.SubscribeAdded.value}, "
                f"status={response.status_code}"
            )
        except requests.RequestException as err:
            status_code = getattr(getattr(err, "response", None), "status_code", None)
            target = urlsplit(self._endpoint).netloc or "<invalid>"
            logger.error(
                f"双重订阅转发失败：event={EventType.SubscribeAdded.value}, "
                f"target={target}, error={type(err).__name__}, status={status_code or '-'}"
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

    @classmethod
    def __to_json_value(cls, value: Any, seen=None) -> Any:
        """不修改原对象地转换 MoviePilot 事件数据为 JSON 兼容结构。"""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Enum):
            return cls.__to_json_value(value.value, seen)
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        seen = seen or set()
        value_id = id(value)
        if value_id in seen:
            return "<recursive>"
        seen.add(value_id)
        try:
            if isinstance(value, dict):
                return {
                    str(key): cls.__to_json_value(val, seen)
                    for key, val in value.items()
                }
            if isinstance(value, (list, tuple, set)):
                return [cls.__to_json_value(item, seen) for item in value]
            if hasattr(value, "model_dump"):
                return cls.__to_json_value(value.model_dump(), seen)
            if hasattr(value, "to_dict"):
                return cls.__to_json_value(value.to_dict(), seen)
            if hasattr(value, "dict"):
                return cls.__to_json_value(value.dict(), seen)
            if hasattr(value, "__dict__"):
                return cls.__to_json_value(
                    {
                        key: val
                        for key, val in vars(value).items()
                        if not str(key).startswith("_")
                    },
                    seen,
                )
            return str(value)
        finally:
            seen.discard(value_id)
