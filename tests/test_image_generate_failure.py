from __future__ import annotations

import pytest

from data.payloads import build_valid_image_payload
from utils.config import Settings


@pytest.mark.costly
@pytest.mark.slow
def test_invalid_reference_image_leads_to_task_failure(
    settings: Settings,
    image_task_service,
) -> None:
    """失败回调链路：无效参考图 → 任务异步失败 → 轮询捕获 errorMsg。

    用不存在的参考图 URL 触发后端生成失败（实测：下载 404 → 生图失败）。
    验证 wait_until_finished 能识别失败状态并抛出带 errorMsg 的异常。
    """
    payload = build_valid_image_payload(
        reference_image_url=(
            "https://minio.test.xywhaigc.top/minio/aigc/nonexistent/not-found.png"
        ),
    )

    task_id = image_task_service.submit(payload)

    with pytest.raises(AssertionError) as exc_info:
        image_task_service.wait_until_finished(task_id)

    message = str(exc_info.value)
    assert "失败" in message, f"异常信息应包含失败标记：{message}"
