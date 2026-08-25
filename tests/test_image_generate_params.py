from __future__ import annotations

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


def _submit_and_verify(
    settings: Settings,
    image_api: ImageApi,
    **changes: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """提交带参数变体的任务，校验提交成功 + 任务详情字段回显一致。

    只提交并查询一次详情，不等待生成完成（秒级，避免长时间占用）。
    """
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )
    payload.update(changes)

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
    return payload, task


# ---------------------------------------------------------------------------
# 图片尺寸变体
# ---------------------------------------------------------------------------


@pytest.mark.costly
@pytest.mark.parametrize(
    "image_size",
    [
        "512x512",
        "1024x1024",
        "2048x2048",
    ],
    ids=lambda value: f"size={value}",
)
def test_image_size_variants(
    image_size: str,
    settings: Settings,
    image_api: ImageApi,
) -> None:
    """不同图片尺寸：任务详情 imageSize 应与请求一致。"""
    payload, task = _submit_and_verify(
        settings,
        image_api,
        imageSize=image_size,
    )
    assert task.get("imageSize") == payload["imageSize"], (
        f"imageSize回显不一致，请求={payload['imageSize']!r}，"
        f"响应={task.get('imageSize')!r}"
    )


# ---------------------------------------------------------------------------
# 宽高比变体
# ---------------------------------------------------------------------------


@pytest.mark.costly
@pytest.mark.parametrize(
    "aspect_ratio",
    [
        "1:1",
        "16:9",
        "9:16",
    ],
    ids=lambda value: f"ratio={value}",
)
def test_aspect_ratio_variants(
    aspect_ratio: str,
    settings: Settings,
    image_api: ImageApi,
) -> None:
    """不同宽高比：任务详情 aspectRatio 应与请求一致。"""
    payload, task = _submit_and_verify(
        settings,
        image_api,
        aspectRatio=aspect_ratio,
    )
    assert task.get("aspectRatio") == payload["aspectRatio"], (
        f"aspectRatio回显不一致，请求={payload['aspectRatio']!r}，"
        f"响应={task.get('aspectRatio')!r}"
    )


# ---------------------------------------------------------------------------
# 生成数量变体
# ---------------------------------------------------------------------------


@pytest.mark.costly
@pytest.mark.parametrize(
    "generate_count",
    [1, 2, 4],
    ids=lambda value: f"count={value}",
)
def test_generate_count_variants(
    generate_count: int,
    settings: Settings,
    image_api: ImageApi,
) -> None:
    """不同生成数量：任务详情 generateImgCount 应与请求一致。"""
    payload, task = _submit_and_verify(
        settings,
        image_api,
        generateImgCount=generate_count,
    )
    assert task.get("generateImgCount") == payload["generateImgCount"], (
        f"generateImgCount回显不一致，"
        f"请求={payload['generateImgCount']!r}，"
        f"响应={task.get('generateImgCount')!r}"
    )
