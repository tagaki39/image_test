from __future__ import annotations

import pytest

from data.payloads import build_valid_image_payload
from utils.enums import TaskStatus


# 成功任务必须包含的字段
_REQUIRED_TASK_FIELDS = {
    "id",
    "status",
    "outputUrl",
    "errorMsg",
    "resourceList",
    "model",
    "resolution",
    "imageSize",
    "aspectRatio",
    "generateImgCount",
    "genType",
    "businessType",
    "businessTaskType",
    "projectId",
}


def _assert_task_has_required_fields(task: dict) -> None:
    """确保任务详情包含所有必需字段，缺失时给出明确提示。"""
    missing = _REQUIRED_TASK_FIELDS - task.keys()
    assert not missing, (
        f"任务详情缺少必要字段：{sorted(missing)}，"
        f"实际字段：{sorted(task.keys())}"
    )


@pytest.mark.smoke
@pytest.mark.costly
@pytest.mark.slow
def test_generate_image_success(
    settings,
    image_task_service,
) -> None:
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    task = image_task_service.submit_and_wait(payload)

    # 先校验字段完整性，避免后续下标 KeyError
    _assert_task_has_required_fields(task)

    assert task["status"] == TaskStatus.SUCCESS

    error_msg = task.get("errorMsg")
    assert error_msg is None or error_msg == "", (
        f"成功任务不应存在错误信息：{error_msg!r}"
    )

    assert task["model"] == payload["model"]
    assert task["resolution"] == payload["resolution"]
    assert task["imageSize"] == payload["imageSize"]
    assert task["aspectRatio"] == payload["aspectRatio"]
    assert task["generateImgCount"] == payload["generateImgCount"]
    assert task["genType"] == payload["genType"]
    assert task["businessType"] == payload["businessType"]
    assert task["businessTaskType"] == payload["businessTaskType"]

    # projectId：先校验类型再比较值
    assert isinstance(task["projectId"], int), (
        f"projectId应为整数，实际类型：{type(task['projectId']).__name__}"
    )
    assert task["projectId"] == int(payload["projectId"]), (
        f"projectId不一致，"
        f"请求值={payload['projectId']!r}，"
        f"响应值={task['projectId']!r}"
    )

    # inputFile 在传入时对比
    if payload.get("inputFile"):
        assert task["inputFile"] == payload["inputFile"]

    # outputUrl 后缀校验
    output_url = task["outputUrl"]
    assert isinstance(output_url, str), "outputUrl应为字符串"
    assert output_url.endswith(
        (".png", ".jpg", ".jpeg", ".webp")
    ), f"outputUrl后缀不符合预期：{output_url}"

    # resourceList 关联校验
    assert task["resourceList"]
    assert task["resourceList"][0]["taskId"] == task["id"]
