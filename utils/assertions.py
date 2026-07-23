from __future__ import annotations

from typing import Any

import requests


def assert_http_ok(response: requests.Response) -> None:
    assert response.status_code == 200, (
        f"HTTP状态异常：{response.status_code}\n"
        f"响应内容：{response.text[:2000]}"
    )


def parse_json(response: requests.Response) -> dict[str, Any]:
    try:
        result = response.json()
    except ValueError as exc:
        raise AssertionError(
            f"响应不是合法JSON：{response.text[:2000]}"
        ) from exc

    assert isinstance(result, dict), (
        f"响应JSON应为对象，实际类型：{type(result).__name__}"
    )
    return result


def assert_business_success(
    result: dict[str, Any],
    expected_code: int = 200,
) -> None:
    assert result.get("code") == expected_code, (
        f"业务状态码异常，预期={expected_code}，"
        f"实际={result.get('code')}，"
        f"msg={result.get('msg')}"
    )


def assert_image_response(response: requests.Response) -> None:
    assert response.status_code == 200, (
        f"结果图片不可访问：HTTP {response.status_code}"
    )
    content_type = response.headers.get("Content-Type", "")
    assert content_type.startswith("image/"), (
        f"结果资源不是图片，Content-Type={content_type}"
    )
    assert len(response.content) > 0, "结果图片内容为空"
