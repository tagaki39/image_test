from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

from api.auth_api import AuthApi
from api.image_api import ImageApi
from services.auth_service import AuthService
from services.image_task_service import ImageTaskService
from utils.config import Settings
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
            safe_name = item.name.replace("::", "_").replace("/", "_")[:80]
            file_path = FAILURES_DIR / f"{safe_name}_{report.nodeid.count('::')}.json"
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


@pytest.fixture(scope="session")
def auth_api(settings: Settings) -> AuthApi:
    session = requests.Session()
    return AuthApi(
        session=session,
        base_url=settings.base_url,
        client_id=settings.client_id,
        public_key_b64=settings.rsa_public_key,
    )


@pytest.fixture(scope="session")
def access_token(
    settings: Settings,
    auth_api: AuthApi,
) -> str:
    """自动登录获取最新 Token；未配置登录信息时回退 .env 静态 Token。"""
    if settings.rsa_public_key and settings.login_username:
        service = AuthService(auth_api)
        token = service.login(
            username=settings.login_username,
            password=settings.login_password,
        )
    else:
        token = settings.authorization.removeprefix("Bearer ").strip()
    return token


@pytest.fixture(scope="session")
def api_session(
    settings: Settings,
    access_token: str,
) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {access_token}",
            "clientid": settings.client_id,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
        }
    )
    yield session
    session.close()


@pytest.fixture(scope="session")
def image_api(
    api_session: requests.Session,
    settings: Settings,
) -> ImageApi:
    return ImageApi(
        session=api_session,
        base_url=settings.base_url,
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
