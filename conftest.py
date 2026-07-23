from __future__ import annotations

import os

import pytest
import requests
from dotenv import load_dotenv

from api.image_api import ImageApi
from services.image_task_service import ImageTaskService
from utils.config import Settings


load_dotenv()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def api_session(settings: Settings) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": settings.authorization,
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
