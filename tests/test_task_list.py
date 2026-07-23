from __future__ import annotations

import pytest

from utils.assertions import assert_http_ok, parse_json


@pytest.mark.smoke
def test_resource_task_list_structure(image_api) -> None:
    """任务列表只测试历史记录和分页结构，不再参与生成任务轮询。"""
    response = image_api.list_tasks(
        business_type=1,
        page_num=1,
        page_size=5,
    )

    assert_http_ok(response)
    result = parse_json(response)

    assert isinstance(result.get("total"), int)
    assert isinstance(result.get("rows"), list)
    assert len(result["rows"]) <= 5

    if result["rows"]:
        task = result["rows"][0]
        assert "id" in task
        assert "status" in task
        assert "outputUrl" in task
        assert "errorMsg" in task
        assert "resourceList" in task
