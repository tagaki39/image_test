from __future__ import annotations

import requests

from utils.http_client import HttpClient


class BillApi:
    BILL_STAT_LIST_PATH = "/prod-api/bill/stat/list"

    def __init__(self, http_client: HttpClient) -> None:
        self.http_client = http_client

    def get_bill_stat_list(
        self,
        *,
        biz_id: str,
        biz_type: int = 1,
        timeout: int = 60,
    ) -> requests.Response:
        """账单统计列表：bizId 即生成任务返回的 taskId。"""
        return self.http_client.get(
            self.BILL_STAT_LIST_PATH,
            params={
                "bizType": biz_type,
                "bizId": biz_id,
            },
            timeout=timeout,
        )
