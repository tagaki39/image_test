from __future__ import annotations

from typing import Any

import requests

from utils.recorder import record_request, record_response


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
        url = f"{self.base_url}{self.GENERATE_PATH}"
        record_request("POST", url, self.session.headers, payload)
        response = self.session.post(url, json=payload, timeout=timeout)
        record_response(response)
        return response

    def get_task_detail(
        self,
        task_id: str,
        timeout: int = 30,
    ) -> requests.Response:
        path = self.TASK_DETAIL_PATH.format(task_id=task_id)
        url = f"{self.base_url}{path}"
        record_request("GET", url, self.session.headers)
        response = self.session.get(url, timeout=timeout)
        record_response(response)
        return response

    def list_tasks(
        self,
        *,
        business_type: int = 1,
        page_num: int = 1,
        page_size: int = 100,
        timeout: int = 30,
    ) -> requests.Response:
        """历史任务列表接口，仅用于列表功能测试，不用于任务轮询。"""
        params = {
            "businessType": business_type,
            "pageNum": page_num,
            "pageSize": page_size,
        }
        url = f"{self.base_url}{self.TASK_LIST_PATH}"
        record_request("GET", url, self.session.headers, params)
        response = self.session.get(url, params=params, timeout=timeout)
        record_response(response)
        return response

    @staticmethod
    def get_resource(
        url: str,
        timeout: int = 30,
    ) -> requests.Response:
        record_request("GET", url)
        response = requests.get(url, timeout=timeout)
        record_response(response)
        return response
