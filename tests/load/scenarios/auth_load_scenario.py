import base64
import hashlib
import hmac
import json
import random
import time
from typing import Any, Dict

SECRET_KEY = "load-test-secret-key-balance-plus"
USER_POOL_SIZE = 500


def base64url_encode(data: bytes) -> str:
    """Кодирование в Base64URL без паддинга согласно RFC 7515/7519."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def generate_jwt(user_id: int, username: str, expires_in: int = 300) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "username": username,
        "name": f"Инженер {username}",
        "role": "engineer",
        "iat": now,
        "exp": now + expires_in,
    }

    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


class UserPoolManager:
    def __init__(self, size: int = USER_POOL_SIZE):
        self.users: list[Dict[str, Any]] = []
        for i in range(1, size + 1):
            username = f"engineer_{i}"
            self.users.append({
                "user_id": i,
                "username": username,
                "token": generate_jwt(i, username, expires_in=180),
                "created_at": time.time(),
            })

    def get_random_user(self) -> Dict[str, Any]:
        return random.choice(self.users)

    def rotate_user_token(self, user: Dict[str, Any], expires_in: int = 300) -> str:
        """Симуляция ротации токена сессии."""
        new_token = generate_jwt(user["user_id"], user["username"], expires_in=expires_in)
        user["token"] = new_token
        user["created_at"] = time.time()
        return new_token


user_pool = UserPoolManager()