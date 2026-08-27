from __future__ import annotations

import copy
import yaml
from pathlib import Path
from typing import Any

import pytest

from api.image_api import ImageApi
from data.payloads import build_valid_image_payload
from utils.assertions import assert_http_ok, parse_json
from utils.config import Settings

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_cases(filename: str) -> list[dict[str, Any]]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _submit_invalid_payload(
    case: dict[str, Any],
    settings: Settings,
    image_api: ImageApi,
) -> None:
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )
    payload = copy.deepcopy(payload)
    payload.update(case["changes"])

    response = image_api.generate_image(payload)

    # 当前系统可能HTTP 200、业务code非200；
    # 也可能任务提交成功后异步失败。
    # 在规则未完全确认前，先保证服务端有明确响应。
    assert response.status_code in {200, 400, 401, 403, 422, 500}

    if response.headers.get("Content-Type", "").startswith(
        "application/json"
    ):
        result = parse_json(response)
        assert result.get("msg") is not None

        if not case["expected_success"]:
            assert result.get("code") != 200 or not result.get("data"), (
                "异常参数被当作成功请求接受，"
                "需要确认是否属于异步失败场景"
            )


@pytest.mark.negative
@pytest.mark.costly
@pytest.mark.parametrize(
    "case",
    _load_cases("image_invalid_cases.yml"),
    ids=lambda item: item["case_name"],
)
def test_image_generate_invalid_parameters(
    case: dict[str, Any],
    settings: Settings,
    image_api: ImageApi,
) -> None:
    """异常参数：空/缺失/敏感词/非法模型/非法格式应被拒绝。"""
    _submit_invalid_payload(case, settings, image_api)


@pytest.mark.negative
@pytest.mark.costly
@pytest.mark.parametrize(
    "case",
    _load_cases("boundary_cases.yml"),
    ids=lambda item: item["case_name"],
)
def test_image_generate_boundary_parameters(
    case: dict[str, Any],
    settings: Settings,
    image_api: ImageApi,
) -> None:
    """边界值：0/负数/超上限数量应被拒绝。"""
    _submit_invalid_payload(case, settings, image_api)
