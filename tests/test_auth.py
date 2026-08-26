from __future__ import annotations

import requests
import pytest

from data.payloads import build_valid_image_payload
from utils.config import Settings


def _assert_auth_rejected(response: requests.Response) -> None:
    """断言请求被鉴权拦截：HTTP 401/403 或 HTTP 200+业务码 401/403。"""
    assert response.status_code in {200, 401, 403}

    if response.headers.get("Content-Type", "").startswith(
        "application/json"
    ):
        result = response.json()
        assert result.get("code") in {401, 403} or response.status_code in {
            401,
            403,
        }, (
            f"鉴权失败但业务码异常：code={result.get('code')}，"
            f"msg={result.get('msg')}"
        )


@pytest.mark.auth
def test_generate_image_without_authorization(
    settings: Settings,
) -> None:
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    response = requests.post(
        f"{settings.base_url}/prod-api/aigc/task/generateImage",
        json=payload,
        headers={
            "clientid": settings.client_id,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
        },
        timeout=30,
    )

    _assert_auth_rejected(response)


@pytest.mark.auth
def test_generate_image_with_expired_token(
    settings: Settings,
) -> None:
    """过期/伪造 Token 应被拒绝，不创建任务。

    实测后端拒绝方式：HTTP 200 + 业务 code 401（认证失败），
    也可能 HTTP 401/403，两种都接受。
    """
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    response = requests.post(
        f"{settings.base_url}/prod-api/aigc/task/generateImage",
        json=payload,
        headers={
            "Authorization": "Bearer expired.invalid.token",
            "clientid": settings.client_id,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
        },
        timeout=30,
    )

    _assert_auth_rejected(response)


@pytest.mark.auth
def test_generate_image_without_clientid(
    settings: Settings,
) -> None:
    """缺少 clientid 应被拒绝（401/403），不创建任务。"""
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    response = requests.post(
        f"{settings.base_url}/prod-api/aigc/task/generateImage",
        json=payload,
        headers={
            "Authorization": settings.authorization,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
        },
        timeout=30,
    )

    _assert_auth_rejected(response)
