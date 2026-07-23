from __future__ import annotations

from typing import Any


def build_valid_image_payload(
    *,
    reference_image_url: str = "",
) -> dict[str, Any]:
    """
    默认构造图生图请求。
    没有参考图时，可传空字符串，并根据实际前端规则调整genType/inputFile。
    """
    return {
        "name": "pytest图片生成冒烟测试",
        "projectId": "1",
        "categoryId": None,
        "prompt": (
            "一只小麻雀站在开满粉色花朵的树枝上，"
            "清晨阳光透过树叶形成斑驳光影，"
            "自然写实摄影风格，居中构图。"
        ),
        "generateImgCount": 1,
        "forceSingleImg": 1,
        "priority": 2,
        "model": "doubao-seedream-5-0-pro-260628",
        "businessType": 1,
        "genType": 2,
        "imageSize": "1024x1024",
        "resolution": "1K",
        "aspectRatio": "1:1",
        "inputFile": reference_image_url,
        "businessTaskType": 8,
    }
