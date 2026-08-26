from __future__ import annotations

import os
from dataclasses import dataclass


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"缺少必要环境变量：{name}")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    base_url: str
    authorization: str
    client_id: str
    reference_image_url: str
    task_timeout_seconds: int
    poll_interval_seconds: int
    task_list_page_size: int
    verify_output_image: bool
    login_username: str
    login_password: str
    rsa_public_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            base_url=_required_env("BASE_URL").rstrip("/"),
            authorization=_required_env("AUTHORIZATION"),
            client_id=_required_env("CLIENT_ID"),
            reference_image_url=os.getenv("REFERENCE_IMAGE_URL", "").strip(),
            task_timeout_seconds=int(
                os.getenv("TASK_TIMEOUT_SECONDS", "240")
            ),
            poll_interval_seconds=int(
                os.getenv("POLL_INTERVAL_SECONDS", "5")
            ),
            task_list_page_size=int(
                os.getenv("TASK_LIST_PAGE_SIZE", "100")
            ),
            verify_output_image=_env_bool(
                "VERIFY_OUTPUT_IMAGE",
                True,
            ),
            # 自动登录配置（可选）：配置后每次运行自动登录获取最新 Token
            login_username=os.getenv("LOGIN_USERNAME", "").strip(),
            login_password=os.getenv("LOGIN_PASSWORD", "").strip(),
            rsa_public_key=os.getenv("RSA_PUBLIC_KEY", "").strip(),
        )
