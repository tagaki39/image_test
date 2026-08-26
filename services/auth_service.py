from __future__ import annotations

from api.auth_api import AuthApi
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

        data = result.get("data")
        assert isinstance(data, dict), (
            "登录接口返回的data应为对象，"
            f"实际类型={type(data).__name__}"
        )

        access_token = data.get("access_token")
        assert isinstance(access_token, str), (
            "登录成功但access_token类型异常，"
            f"实际类型={type(access_token).__name__}"
        )
        assert access_token.strip(), "登录成功但access_token为空"

        return access_token
