from __future__ import annotations

from typing import Any, Callable

import requests

from utils.recorder import record_request, record_response

AuthRefresh = Callable[[], str | None]


class HttpClient:
    """统一请求客户端：headers 合并、超时、请求/响应记录、401 自动重新认证。

    架构：Tests → Service → API → HttpClient → Requests
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: int = 30,
        auth_refresh: AuthRefresh | None = None,
    ) -> None:
        self.session = requests.Session()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._auth_refresh = auth_refresh
        if headers:
            self.session.headers.update(headers)

    # ------------------------------------------------------------------
    # 对外方法
    # ------------------------------------------------------------------

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        return self.request("GET", path, params=params, timeout=timeout)

    def post(
        self,
        path: str,
        *,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
        data: Any = None,
        timeout: int | None = None,
        retry_auth: bool = True,
    ) -> requests.Response:
        return self.request(
            "POST",
            path,
            json_body=json_body,
            headers=headers,
            data=data,
            timeout=timeout,
            retry_auth=retry_auth,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
        retry_auth: bool = True,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        merged_headers = dict(self.session.headers)
        merged_headers.update(headers or {})

        response = self._send(
            method, url, merged_headers, json_body, data, params, timeout
        )

        # 401 自动重新认证并重试一次（仅一次，防死循环）
        if (
            retry_auth
            and self._auth_refresh is not None
            and self._is_unauthorized(response)
        ):
            new_token = self._auth_refresh()
            if new_token:
                self.session.headers["Authorization"] = f"Bearer {new_token}"
                # 重新合并 headers（含新 Token），否则重试仍带旧值
                retry_headers = dict(self.session.headers)
                retry_headers.update(headers or {})
                response = self._send(
                    method, url, retry_headers, json_body, data, params, timeout
                )

        return response

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _send(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        json_body: Any,
        data: Any,
        params: dict[str, Any] | None,
        timeout: int | None,
    ) -> requests.Response:
        record_request(method, url, headers, json_body or data or params)
        response = self.session.request(
            method,
            url,
            headers=headers,
            json=json_body,
            data=data,
            params=params,
            timeout=timeout or self.timeout,
        )
        record_response(response)
        return response

    @staticmethod
    def _is_unauthorized(response: requests.Response) -> bool:
        """识别鉴权失败：HTTP 401/403，或 HTTP 200 + 业务码 401/403。"""
        if response.status_code in (401, 403):
            return True
        try:
            data = response.json()
        except ValueError:
            return False
        return isinstance(data, dict) and data.get("code") in (401, 403)
