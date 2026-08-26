from __future__ import annotations

import time
from typing import Any

import requests

"""请求/响应记录器：供失败现场采集使用（见 conftest.py）。"""

_last_request: dict[str, Any] | None = None
_last_response: dict[str, Any] | None = None


def record_request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: Any = None,
) -> None:
    """记录最近一次请求（脱敏 Authorization/encrypt-key）。"""
    global _last_request
    safe_headers = dict(headers or {})
    for key in ("Authorization", "encrypt-key"):
        if key in safe_headers:
            safe_headers[key] = "****"
    _last_request = {
        "method": method,
        "url": url,
        "headers": safe_headers,
        "body": body,
    }


def record_response(response: requests.Response) -> None:
    """记录最近一次响应（截断防止超大内容）。"""
    global _last_response
    _last_response = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.text[:5000],
    }


def clear() -> None:
    """清空记录（每个测试开始前调用）。"""
    global _last_request, _last_response
    _last_request = None
    _last_response = None


def snapshot() -> dict[str, Any]:
    """导出当前记录的请求/响应快照（供失败保存）。"""
    return {
        "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "request": _last_request,
        "response": _last_response,
    }
