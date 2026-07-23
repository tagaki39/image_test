from __future__ import annotations

import pytest

from data.payloads import build_valid_image_payload
from utils.assertions import (
    assert_business_success,
    assert_http_ok,
    parse_json,
)


@pytest.mark.smoke
@pytest.mark.costly
def test_submit_image_task_returns_task_id(
    settings,
    image_api,
) -> None:
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    response = image_api.generate_image(payload)

    assert_http_ok(response)
    result = parse_json(response)
    assert_business_success(result)

    # msg 只需存在且非空，不绑定具体中文文案
    msg = result.get("msg")
    assert isinstance(msg, str) and msg.strip(), (
        f"msg字段异常：{msg!r}"
    )

    task_data = result.get("data")
    assert str(task_data).isdigit(), (
        f"任务ID格式异常：{task_data!r}"
    )
