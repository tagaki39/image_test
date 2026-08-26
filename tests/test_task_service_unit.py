from __future__ import annotations

from typing import Any

import pytest

from services.image_task_service import ImageTaskService


class FakeResponse:
    """模拟 requests.Response，供单元测试注入。"""

    def __init__(self, status_code: int = 200, json_data: dict[str, Any] | None = None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self) -> dict[str, Any]:
        return self._json


def _make_service(task_payloads: list[dict[str, Any]], **kwargs) -> ImageTaskService:
    """构造 Service，get_task_detail 按列表顺序返回任务详情。"""
    api = type(
        "FakeApi",
        (),
        {
            # 仅 1 个元素时无限重复（模拟任务一直处于该状态）
            "get_task_detail": lambda self, task_id: FakeResponse(
                json_data={
                    "code": 200,
                    "msg": "成功",
                    "data": (
                        task_payloads[0]
                        if len(task_payloads) == 1
                        else task_payloads.pop(0)
                    ),
                }
            ),
            "generate_image": lambda self, payload: FakeResponse(
                json_data={"code": 200, "msg": "成功", "data": "1001"}
            ),
            "get_resource": lambda self, url: FakeResponse(
                status_code=200,
                json_data={},
            ),
        },
    )()
    return ImageTaskService(
        image_api=api,
        poll_interval_seconds=0,
        **kwargs,
    )


def test_wait_until_finished_times_out() -> None:
    """任务一直处于生成中状态，超时后应抛出超时错误。"""
    service = _make_service(
        [{"id": "1001", "status": 2}],
        timeout_seconds=0.05,
        verify_output_image=False,
    )
    with pytest.raises(AssertionError, match="超时"):
        service.wait_until_finished("1001")


def test_wait_until_finished_rejects_unknown_status() -> None:
    """出现未定义状态码（如99），应立即失败而非静默轮询。"""
    service = _make_service(
        [{"id": "1001", "status": 99}],
        verify_output_image=False,
    )
    with pytest.raises(AssertionError, match="未定义的任务状态"):
        service.wait_until_finished("1001")


def test_wait_until_finished_failed_status() -> None:
    """任务失败状态（4）应抛出带 errorMsg 的失败信息。"""
    service = _make_service(
        [{"id": "1001", "status": 4, "errorMsg": "模型内部错误"}],
        verify_output_image=False,
    )
    with pytest.raises(AssertionError, match="任务执行失败") as exc_info:
        service.wait_until_finished("1001")
    assert "模型内部错误" in str(exc_info.value)


def test_wait_until_finished_success_with_error_msg() -> None:
    """成功状态（3）但携带 errorMsg，应视为异常。"""
    service = _make_service(
        [{"id": "1001", "status": 3, "errorMsg": "不应存在的错误"}],
        verify_output_image=False,
    )
    with pytest.raises(AssertionError, match="不应存在错误信息"):
        service.wait_until_finished("1001")
