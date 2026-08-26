from __future__ import annotations

from typing import Any

import requests

from utils.http_client import HttpClient


class ImageApi:
    GENERATE_PATH = "/prod-api/aigc/task/generateImage"
    TASK_DETAIL_PATH = "/prod-api/aigc/task/{task_id}"
    TASK_LIST_PATH = "/prod-api/aigc/task/resourceTaskList"

    def __init__(
        self,
        http_client: HttpClient,
    ) -> None:
        self.http_client = http_client

    def generate_image(
        self,
        payload: dict[str, Any],
        timeout: int = 30,
    ) -> requests.Response:
        return self.http_client.post(
            self.GENERATE_PATH,
            json_body=payload,
            timeout=timeout,
        )

    def get_task_detail(
        self,
        task_id: str,
        timeout: int = 30,
    ) -> requests.Response:
        path = self.TASK_DETAIL_PATH.format(task_id=task_id)
        return self.http_client.get(path, timeout=timeout)

    def list_tasks(
        self,
        *,
        business_type: int = 1,
        page_num: int = 1,
        page_size: int = 100,
        timeout: int = 30,
    ) -> requests.Response:
        """历史任务列表接口，仅用于列表功能测试，不用于任务轮询。"""
        return self.http_client.get(
            self.TASK_LIST_PATH,
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
        """下载结果图片（CDN，无需鉴权头）。"""
        from utils.recorder import record_request, record_response

        record_request("GET", url)
        response = requests.get(url, timeout=timeout)
        record_response(response)
        return response
