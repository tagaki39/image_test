from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ResourceItem(BaseModel):
    """任务资源项。"""

    taskId: str | int | None = None
    outputUrl: str | None = None


class TaskDetail(BaseModel):
    """任务详情响应模型：后端字段类型变化时，收集阶段即失败。"""

    model_config = ConfigDict(extra="ignore")

    id: str | int
    status: int
    outputUrl: str | None = None
    errorMsg: str | None = None
    model: str | None = None
    resolution: str | None = None
    imageSize: str | None = None
    aspectRatio: str | None = None
    generateImgCount: int | None = None
    genType: int | None = None
    businessType: int | None = None
    businessTaskType: int | None = None
    projectId: int | None = None
    inputFile: str | None = None
    resourceList: list[Any] | None = None
