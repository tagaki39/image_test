from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

from api.auth_api import AuthApi
from api.bill_api import BillApi
from api.image_api import ImageApi
from services.auth_service import AuthService
from services.bill_service import BillService
from services.image_task_service import ImageTaskService
from utils.config import Settings
from utils.http_client import HttpClient
from utils.recorder import clear as clear_recorder
from utils.recorder import snapshot as recorder_snapshot


load_dotenv()

FAILURES_DIR = Path("reports/failures")


def pytest_configure(config) -> None:
    """保证报告目录存在（pytest-html 不会自动创建）。"""
    os.makedirs("reports", exist_ok=True)
    FAILURES_DIR.mkdir(parents=True, exist_ok=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试失败时自动保存请求/响应现场到 reports/failures/。"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        snapshot = recorder_snapshot()
        if snapshot["request"] or snapshot["response"]:
            # 参数化 id 可能含 \ / [ ] 等非法文件名字符，统一清洗
            safe_name = re.sub(r'[\\/:*?"<>|]', "_", item.name)[:60]
            file_path = FAILURES_DIR / f"{safe_name}_{time.time_ns()}.json"
            file_path.write_text(
                json.dumps(snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )


@pytest.fixture(autouse=True)
def _reset_recorder():
    """每个测试开始前清空请求/响应记录。"""
    clear_recorder()
    yield
    clear_recorder()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


def _build_auth_api(settings: Settings) -> AuthApi:
    """构造独立登录客户端（不走 401 重试，防递归）。"""
    http_client = HttpClient(
        base_url=settings.base_url,
        headers={"clientid": settings.client_id},
    )
    return AuthApi(
        http_client=http_client,
        client_id=settings.client_id,
        public_key_b64=settings.rsa_public_key,
    )


def _build_access_token(settings: Settings) -> str:
    """自动登录获取最新 Token；未配置登录信息时回退 .env 静态 Token。"""
    if settings.rsa_public_key and settings.login_username:
        service = AuthService(_build_auth_api(settings))
        return service.login(
            username=settings.login_username,
            password=settings.login_password,
        )
    return settings.authorization.removeprefix("Bearer ").strip()


@pytest.fixture(scope="session")
def auth_api(settings: Settings) -> AuthApi:
    return _build_auth_api(settings)


@pytest.fixture(scope="session")
def access_token(settings: Settings) -> str:
    """自动登录获取最新 Token；未配置登录信息时回退 .env 静态 Token。"""
    return _build_access_token(settings)


@pytest.fixture(scope="session")
def http_client(
    settings: Settings,
    access_token: str,
) -> HttpClient:
    """统一请求客户端，携带 401 自动重新认证回调。"""
    def _refresh_token() -> str | None:
        """401 时自动重新登录一次（仅一次，防死循环）。"""
        if settings.rsa_public_key and settings.login_username:
            return _build_access_token(settings)
        return None

    client = HttpClient(
        base_url=settings.base_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "clientid": settings.client_id,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
        },
        auth_refresh=_refresh_token,
    )
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def image_api(http_client: HttpClient) -> ImageApi:
    return ImageApi(http_client=http_client)


@pytest.fixture(scope="session")
def bill_api(http_client: HttpClient) -> BillApi:
    return BillApi(http_client=http_client)


@pytest.fixture(scope="session")
def bill_service(bill_api: BillApi) -> BillService:
    return BillService(
        bill_api=bill_api,
        timeout_seconds=60,
        poll_interval_seconds=2,
    )


@pytest.fixture(scope="session")
def image_task_service(
    image_api: ImageApi,
    settings: Settings,
) -> ImageTaskService:
    return ImageTaskService(
        image_api=image_api,
        timeout_seconds=settings.task_timeout_seconds,
        poll_interval_seconds=settings.poll_interval_seconds,
        verify_output_image=settings.verify_output_image,
    )
