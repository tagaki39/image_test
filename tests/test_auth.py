from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

import pytest
import requests

from data.payloads import build_valid_image_payload
from utils.config import Settings

AUTH_CASES_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "auth_cases.yml"
)


def _load_auth_cases() -> list[dict[str, Any]]:
    with AUTH_CASES_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


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
@pytest.mark.parametrize(
    "case",
    _load_auth_cases(),
    ids=lambda item: item["case_name"],
)
def test_generate_image_auth_rejection(
    case: dict[str, Any],
    settings: Settings,
) -> None:
    """鉴权失败场景：无Token/过期Token/缺clientid 应被拦截。

    新增场景只需在 data/auth_cases.json 加数据。
    """
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    headers = {
        "clientid": settings.client_id,
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json",
    }

    if not case.get("remove_authorization"):
        authorization = (
            "Bearer expired.invalid.token"
            if case.get("expired_token")
            else settings.authorization
        )
        headers["Authorization"] = authorization

    if case.get("remove_clientid"):
        headers.pop("clientid", None)

    response = requests.post(
        f"{settings.base_url}/prod-api/aigc/task/generateImage",
        json=payload,
        headers=headers,
        timeout=30,
    )

    _assert_auth_rejected(response)
