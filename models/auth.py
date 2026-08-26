from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LoginData(BaseModel):
    """登录响应 data 字段。"""

    model_config = ConfigDict(extra="ignore")

    access_token: str | None = None


class LoginResponse(BaseModel):
    """登录接口响应模型。"""

    model_config = ConfigDict(extra="ignore")

    code: int
    msg: str | None = None
    data: LoginData | None = None
