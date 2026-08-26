from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from api.image_api import ImageApi
from data.payloads import build_valid_image_payload
from utils.assertions import (
    assert_business_success,
    assert_http_ok,
    parse_json,
)
from utils.config import Settings

VALID_CASES_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "image_valid_cases.json"
)


def _load_valid_cases() -> list[dict[str, Any]]:
    with VALID_CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.costly
@pytest.mark.parametrize(
    "case",
    _load_valid_cases(),
    ids=lambda item: item["case_name"],
)
def test_image_generate_valid_variants(
    case: dict[str, Any],
    settings: Settings,
    image_api: ImageApi,
) -> None:
    """参数变体（尺寸/比例/数量）：提交后校验任务详情字段回显一致。

    只提交并查询一次详情，不等待生成完成（秒级，避免长时间占用）。
    新增变体只需在 data/image_valid_cases.json 加数据。
    """
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )
    payload.update(case["changes"])

    response = image_api.generate_image(payload)
    assert_http_ok(response)
    result = parse_json(response)
    assert_business_success(result)

    task_id = str(result.get("data", ""))
    assert task_id.isdigit(), f"任务ID格式异常：{task_id!r}"

    detail_response = image_api.get_task_detail(task_id)
    assert_http_ok(detail_response)
    detail = parse_json(detail_response)
    assert_business_success(detail)

    task = detail.get("data")
    assert isinstance(task, dict), "任务详情data应为对象"

    # 逐字段校验回显一致
    for field in ("imageSize", "aspectRatio", "generateImgCount"):
        if field in case["changes"]:
            assert task.get(field) == payload[field], (
                f"{field}回显不一致，请求={payload[field]!r}，"
                f"响应={task.get(field)!r}"
            )
