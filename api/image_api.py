from __future__ import annotations

from typing import Any

import requests


class ImageApi:
    GENERATE_PATH = "/prod-api/aigc/task/generateImage"
    TASK_DETAIL_PATH = "/prod-api/aigc/task/{task_id}"
    TASK_LIST_PATH = "/prod-api/aigc/task/resourceTaskList"

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")

    def generate_image(
        self,
        payload: dict[str, Any],
        timeout: int = 30,
    ) -> requests.Response:
        return self.session.post(
            f"{self.base_url}{self.GENERATE_PATH}",
            json=payload,
            timeout=timeout,
        )

    def get_task_detail(
        self,
        task_id: str,
        timeout: int = 30,
    ) -> requests.Response:
        path = self.TASK_DETAIL_PATH.format(task_id=task_id)
        return self.session.get(
            f"{self.base_url}{path}",
            timeout=timeout,
        )

    def list_tasks(
        self,
        *,
        business_type: int = 1,
        page_num: int = 1,
        page_size: int = 100,
        timeout: int = 30,
    ) -> requests.Response:
        """历史任务列表接口，仅用于列表功能测试，不用于任务轮询。"""
        return self.session.get(
            f"{self.base_url}{self.TASK_LIST_PATH}",
            params={
                "businessType": business_type,
                "pageNum": page_num,
                "pageSize": page_size,
            },
            timeout=timeout,
        )

    @staticmethod
    def get_resource(
        url: str,
        timeout: int = 30,
    ) -> requests.Response:
        return requests.get(url, timeout=timeout)
