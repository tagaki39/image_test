from __future__ import annotations

from enum import IntEnum


class TaskStatus(IntEnum):
    """图片任务状态枚举（后端约定）。"""

    IN_PROGRESS = 0
    QUEUED = 1
    GENERATING = 2
    SUCCESS = 3
    FAILED = 4


class BusinessCode(IntEnum):
    """业务响应码。"""

    SUCCESS = 200
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    SERVER_ERROR = 500
