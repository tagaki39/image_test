from __future__ import annotations

import os

import pytest
import requests
from dotenv import load_dotenv

from api.auth_api import AuthApi
from api.image_api import ImageApi
from services.auth_service import AuthService
from services.image_task_service import ImageTaskService
from utils.config import Settings


load_dotenv()


def pytest_configure(config) -> None:
    """保证报告目录存在（pytest-html 不会自动创建）。"""
    os.makedirs("reports", exist_ok=True)


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
