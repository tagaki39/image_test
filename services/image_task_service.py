from __future__ import annotations

import time
from typing import Any

import requests

from api.image_api import ImageApi
from utils.assertions import (
    assert_business_success,
    assert_http_ok,
    assert_image_response,
    parse_json,
)
from utils.enums import TaskStatus


class ImageTaskService:
    # 进行中状态集合：0=待提交 1=排队中 2=生成中
    IN_PROGRESS_STATUSES = {
        TaskStatus.IN_PROGRESS,
        TaskStatus.QUEUED,
        TaskStatus.GENERATING,
    }
    SUCCESS_STATUS = TaskStatus.SUCCESS
    FAILED_STATUS = TaskStatus.FAILED

    def __init__(
        self,
        *,
        image_api: ImageApi,
        timeout_seconds: int = 240,
        poll_interval_seconds: int = 5,
        verify_output_image: bool = True,
    ) -> None:
        self.image_api = image_api
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.verify_output_image = verify_output_image

    def submit(self, payload: dict[str, Any]) -> str:
        response = self.image_api.generate_image(payload)
        assert_http_ok(response)

        result = parse_json(response)
        assert_business_success(result)

        task_id = result.get("data")
        assert task_id is not None, "提交成功但未返回任务ID"
        assert str(task_id).strip(), "任务ID为空"
        return str(task_id)

    def get_task(self, task_id: str) -> dict[str, Any]:
        response = self.image_api.get_task_detail(task_id)
        assert_http_ok(response)

        result = parse_json(response)
        assert_business_success(result)

        task = result.get("data")
        assert isinstance(task, dict), (
            "任务详情data应为对象，"
            f"实际类型：{type(task).__name__}"
        )
        assert str(task.get("id")) == str(task_id), (
            "任务详情ID不一致，"
            f"预期={task_id}，实际={task.get('id')}"
        )
        return task

    def wait_until_finished(self, task_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout_seconds
        last_status: Any = None

        while time.monotonic() < deadline:
            task = self.get_task(task_id)
            status = task.get("status")
            last_status = status

            if status == self.SUCCESS_STATUS:
                self._assert_success_task(task)
                return task

            if status == self.FAILED_STATUS:
                raise AssertionError(
                    "图片生成失败："
                    f"taskId={task_id}，"
                    f"errorMsg={task.get('errorMsg')}"
                )

            if status in self.IN_PROGRESS_STATUSES:
                time.sleep(self.poll_interval_seconds)
                continue

            raise AssertionError(
                "发现未定义的任务状态："
                f"taskId={task_id}，"
                f"status={status!r}"
            )

        raise AssertionError(
            "图片生成超时："
            f"taskId={task_id}，"
            f"等待超过{self.timeout_seconds}秒，"
            f"最后状态={last_status!r}"
        )

    def submit_and_wait(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        task_id = self.submit(payload)
        return self.wait_until_finished(task_id)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _assert_success_task(self, task: dict[str, Any]) -> None:
        assert task.get("status") == self.SUCCESS_STATUS

        error_msg = task.get("errorMsg")
        assert error_msg is None or error_msg == "", (
            f"成功任务不应存在错误信息：{error_msg!r}"
        )

        output_url = task.get("outputUrl")
        assert isinstance(output_url, str) and output_url.strip(), (
            "生成成功但outputUrl为空"
        )

        resource_list = task.get("resourceList")
        assert isinstance(resource_list, list), "resourceList应为数组"
        assert len(resource_list) > 0, "生成成功但resourceList为空"

        first_resource = resource_list[0]
        assert str(first_resource.get("taskId")) == str(task.get("id")), (
            "资源关联的taskId与任务ID不一致"
        )
        assert first_resource.get("outputUrl"), "资源outputUrl为空"

        if self.verify_output_image:
            self._verify_output_resource(output_url)

    def _verify_output_resource(self, output_url: str) -> None:
        try:
            response = self.image_api.get_resource(output_url)
        except requests.RequestException as exc:
            raise AssertionError(
                f"生成结果不可访问，url={output_url!r}，原因={exc}"
            ) from exc
        assert_image_response(response)
