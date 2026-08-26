from __future__ import annotations

import base64
import json
import random
import string
from typing import Any

import requests
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad

from utils.http_client import HttpClient


class AuthApi:
    LOGIN_PATH = "/prod-api/auth/login"

    def __init__(
        self,
        http_client: HttpClient,
        client_id: str,
        public_key_b64: str,
    ) -> None:
        self.http_client = http_client
        self.client_id = client_id
        self.public_key_b64 = public_key_b64

    @staticmethod
    def _generate_aes_key() -> bytes:
        """对齐前端：随机32位大小写字母+数字，UTF-8编码作为AES key。"""
        chars = string.ascii_letters + string.digits
        key = "".join(random.choice(chars) for _ in range(32))
        return key.encode("utf-8")

    @staticmethod
    def _aes_encrypt(
        payload: dict[str, Any],
        aes_key: bytes,
    ) -> str:
        """对齐前端 CryptoJS：AES-256-ECB + PKCS7，返回 Base64。"""
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        cipher = AES.new(aes_key, AES.MODE_ECB)
        encrypted = cipher.encrypt(pad(raw, AES.block_size))

        return base64.b64encode(encrypted).decode("utf-8")

    def _rsa_encrypt_aes_key(self, aes_key: bytes) -> str:
        """对齐前端：Base64(AES Key) → RSA PKCS#1 v1.5 公钥加密 → Base64。"""
        aes_key_base64 = base64.b64encode(aes_key).decode("utf-8")

        public_key_der = base64.b64decode(self.public_key_b64)
        public_key = RSA.import_key(public_key_der)

        cipher = PKCS1_v1_5.new(public_key)
        encrypted = cipher.encrypt(aes_key_base64.encode("utf-8"))

        return base64.b64encode(encrypted).decode("utf-8")

    def login(
        self,
        username: str,
        password: str,
        timeout: int = 30,
    ) -> requests.Response:
        assert self.client_id, "client_id为空，请检查CLIENT_ID环境变量"

        payload = {
            "username": username,
            "password": password,
            "clientId": self.client_id,
            "tenantId": "000000",
            "grantType": "password",
        }

        aes_key = self._generate_aes_key()
        encrypted_body = self._aes_encrypt(
            payload=payload,
            aes_key=aes_key,
        )
        encrypt_key = self._rsa_encrypt_aes_key(aes_key)

        headers = {
            "clientid": self.client_id,
            "isEncrypt": "true",
            "encrypt-key": encrypt_key,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
        }

        # 登录接口本身不做 401 重试（防递归）
        return self.http_client.post(
            self.LOGIN_PATH,
            headers=headers,
            data=json.dumps(encrypted_body),
            timeout=timeout,
            retry_auth=False,
        )
