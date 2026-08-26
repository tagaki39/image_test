from __future__ import annotations

from pydantic import ValidationError

from api.auth_api import AuthApi
from models.auth import LoginResponse
from utils.assertions import (
    assert_business_success,
    assert_http_ok,
    parse_json,
)


class AuthService:
    def __init__(self, auth_api: AuthApi) -> None:
        self.auth_api = auth_api

    def login(self, username: str, password: str) -> str:
        response = self.auth_api.login(
            username=username,
            password=password,
        )

        assert_http_ok(response)
        result = parse_json(response)
        assert_business_success(result)

        try:
            login_response = LoginResponse.model_validate(result)
        except ValidationError as exc:
            raise AssertionError(
                f"登录响应字段类型异常：{exc}"
            ) from exc

        access_token = login_response.data.access_token if login_response.data else None
        assert isinstance(access_token, str) and access_token.strip(), (
            "登录成功但access_token缺失或为空"
        )

        return access_token
