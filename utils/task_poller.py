from __future__ import annotations

import time
from typing import Any, Callable

"""通用异步任务轮询器。

图片/视频/音频等异步任务统一复用：
  提交任务 → 轮询详情 → 成功/失败/未知状态/超时处理。
"""

FetchTask = Callable[[str], dict[str, Any]]
SuccessValidator = Callable[[dict[str, Any]], None]


class TaskPoller:
    def __init__(
        self,
        *,
        fetch_task: FetchTask,
        success_status: int,
        failed_status: int,
        in_progress_statuses: set[int],
        timeout_seconds: int,
        poll_interval_seconds: int,
        success_validator: SuccessValidator | None = None,
    ) -> None:
        self.fetch_task = fetch_task
        self.success_status = success_status
        self.failed_status = failed_status
        self.in_progress_statuses = in_progress_statuses
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.success_validator = success_validator

    def wait_until_finished(self, task_id: str) -> dict[str, Any]:
        """轮询直到成功/失败/未知状态/超时，返回最终任务详情。"""
        deadline = time.monotonic() + self.timeout_seconds
        last_status: Any = None

        while time.monotonic() < deadline:
            task = self.fetch_task(task_id)
            status = task.get("status")
            last_status = status

            if status == self.success_status:
                if self.success_validator is not None:
                    self.success_validator(task)
                return task

            if status == self.failed_status:
                raise AssertionError(
                    "任务执行失败："
                    f"taskId={task_id}，"
                    f"errorMsg={task.get('errorMsg')}"
                )

            if status in self.in_progress_statuses:
                time.sleep(self.poll_interval_seconds)
                continue

            raise AssertionError(
                "发现未定义的任务状态："
                f"taskId={task_id}，"
                f"status={status!r}"
            )

        raise AssertionError(
            "任务超时："
            f"taskId={task_id}，"
            f"等待超过{self.timeout_seconds}秒，"
            f"最后状态={last_status!r}"
        )
