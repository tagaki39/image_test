from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from data.payloads import build_valid_image_payload
from services.bill_service import BillService
from utils.config import Settings

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


@pytest.mark.billing
@pytest.mark.costly
@pytest.mark.slow
def test_e2e_image_generation_billing(
    settings: Settings,
    image_task_service,
    bill_service: BillService,
) -> None:
    """E2E 计费：真实生成任务 → 轮询成功 → 当场校验账单积分。

    不写死期望积分（模型价格可能调整），以账单自身为准：
    成功任务的最终结算积分(endCredits) 应等于预估积分(previewCredits) 且 > 0。
    """
    # 参考图 URL 可能失效（minio 会清理），传空串走文生图路径
    payload = build_valid_image_payload(reference_image_url="")

    task = image_task_service.submit_and_wait(payload)
    task_id = str(task["id"])

    bill = bill_service.wait_for_bill(task_id=task_id, biz_type=1)

    actual = bill_service._to_decimal(bill.get("endCredits"), "endCredits")
    preview = bill_service._to_decimal(bill.get("previewCredits"), "previewCredits")

    assert actual == preview, (
        f"成功任务最终积分与预估不一致：taskId={task_id}, "
        f"preview={preview}, end={actual}"
    )
    assert actual > 0, f"积分不应为0或负数：{actual}"

    # 账单与任务字段关联
    assert bill.get("model") == task.get("model"), (
        f"账单model与任务不一致：bill={bill.get('model')}, task={task.get('model')}"
    )
    assert bill.get("taskId") == task_id, "账单taskId与任务不一致"
    assert bill.get("billingUnit"), "billingUnit为空"
