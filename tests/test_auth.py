from __future__ import annotations

import requests
import pytest

from data.payloads import build_valid_image_payload
from utils.config import Settings


@pytest.mark.auth
def test_generate_image_without_authorization(
    settings: Settings,
) -> None:
    payload = build_valid_image_payload(
        reference_image_url=settings.reference_image_url,
    )

    response = requests.post(
        f"{settings.base_url}/prod-api/aigc/task/generateImage",
        json=payload,
        headers={
            "clientid": settings.client_id,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
        },
        timeout=30,
    )

    assert response.status_code in {200, 401, 403}

    if response.headers.get("Content-Type", "").startswith(
        "application/json"
    ):
        result = response.json()
        assert result.get("code") in {401, 403} or response.status_code in {
            401,
            403,
        }
