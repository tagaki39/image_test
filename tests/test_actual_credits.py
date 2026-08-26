from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from services.bill_service import BillService

CASES_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "actual_credit_cases.json"
)


def load_cases() -> list[dict[str, Any]]:
    with CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.billing
@pytest.mark.parametrize(
    "case",
    load_cases(),
    ids=lambda case: case["caseId"],
)
def test_actual_credits(
    case: dict[str, Any],
    bill_service: BillService,
) -> None:
    """实际消耗积分校验：账单存在 + status=3 + endCredits 一致 + 计费字段正确。

    新增计费用例只需在 data/actual_credit_cases.json 加数据。
    """
    bill = bill_service.assert_actual_credits(
        task_id=case["taskId"],
        expected_credits=case["expectedCredits"],
        check_preview=True,
    )

    assert bill["status"] == 3, f"账单状态异常：{bill.get('status')}"
    assert bill["businessType"] == case["businessType"], (
        f"businessType不一致：{bill.get('businessType')}"
    )
    assert bill["businessTaskType"] == case["businessTaskType"], (
        f"businessTaskType不一致：{bill.get('businessTaskType')}"
    )
    assert bill["genType"] == case["genType"], (
        f"genType不一致：{bill.get('genType')}"
    )
    assert bill["model"] == case["model"], (
        f"model不一致：{bill.get('model')}"
    )
    assert bill["billingUnit"] == case["billingUnit"], (
        f"billingUnit不一致：{bill.get('billingUnit')}"
    )
