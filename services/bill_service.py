from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation
from typing import Any

from api.bill_api import BillApi
from utils.assertions import (
    assert_business_success,
    assert_http_ok,
    parse_json,
)


class BillService:
    """账单服务：只负责计费验证，与生成 Service 通过 taskId 关联。

    图片/视频/音频等生成任务均可共用。
    """

    SUCCESS_STATUS = 3

    def __init__(
        self,
        bill_api: BillApi,
        *,
        timeout_seconds: int = 60,
        poll_interval_seconds: int = 2,
    ) -> None:
        self.bill_api = bill_api
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    def get_bill_rows(
        self,
        task_id: str,
        biz_type: int = 1,
    ) -> list[dict[str, Any]]:
        response = self.bill_api.get_bill_stat_list(
            biz_id=task_id,
            biz_type=biz_type,
        )
        assert_http_ok(response)

        result = parse_json(response)
        assert_business_success(result)

        rows = result.get("rows")
        assert isinstance(rows, list), (
            "账单接口rows字段类型异常，"
            f"实际类型={type(rows).__name__}"
        )
        return rows

    def find_bill(
        self,
        task_id: str,
        biz_type: int = 1,
    ) -> dict[str, Any] | None:
        """按 taskId/bizId 精确匹配账单；多版本时取 changeVersion 最新。"""
        rows = self.get_bill_rows(task_id=task_id, biz_type=biz_type)

        matched = [
            row
            for row in rows
            if str(row.get("taskId")) == str(task_id)
            and str(row.get("bizId")) == str(task_id)
        ]
        if not matched:
            return None

        matched.sort(
            key=lambda item: item.get("changeVersion") or 0,
            reverse=True,
        )
        return matched[0]

    def wait_for_bill(
        self,
        task_id: str,
        biz_type: int = 1,
    ) -> dict[str, Any]:
        """轮询等待账单生成（任务成功后账单可能延迟写入数据库）。"""
        deadline = time.monotonic() + self.timeout_seconds

        while time.monotonic() < deadline:
            bill = self.find_bill(task_id=task_id, biz_type=biz_type)

            if bill is None:
                time.sleep(self.poll_interval_seconds)
                continue

            if bill.get("status") == self.SUCCESS_STATUS:
                return bill

            time.sleep(self.poll_interval_seconds)

        raise AssertionError(
            "等待账单生成超时，"
            f"taskId={task_id}, "
            f"timeout={self.timeout_seconds}s"
        )

    @staticmethod
    def _to_decimal(value: Any, field_name: str) -> Decimal:
        """积分/金额用 Decimal 精确比较，避免浮点误差。"""
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise AssertionError(
                f"{field_name}不是合法数值，实际值={value!r}"
            ) from exc

    def assert_actual_credits(
        self,
        *,
        task_id: str,
        expected_credits: str | int | Decimal,
        biz_type: int = 1,
        check_preview: bool = False,
    ) -> dict[str, Any]:
        """校验任务实际消耗积分（endCredits = 最终结算积分）。"""
        bill = self.wait_for_bill(task_id=task_id, biz_type=biz_type)

        actual = self._to_decimal(bill.get("endCredits"), "endCredits")
        expected = self._to_decimal(expected_credits, "expectedCredits")

        assert actual == expected, (
            "实际消耗积分不一致，"
            f"taskId={task_id}, "
            f"expected={expected}, "
            f"actual={actual}"
        )

        if check_preview:
            preview = self._to_decimal(bill.get("previewCredits"), "previewCredits")
            assert preview == expected, (
                "预估积分不一致，"
                f"taskId={task_id}, "
                f"expected={expected}, "
                f"preview={preview}"
            )

        return bill
