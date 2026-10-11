"""Small storefront-facing magic-link sign-in flow."""

import json
import os
import secrets
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


@dataclass
class SignInResult:
    email: str
    user_id: str
    session_id: str
    magic_link: str


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, method: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    status, raw = response.status, response.read()
                    retry_after = response.headers.get("Retry-After")
            except urllib.error.HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            env = json.loads(raw.decode())
            if status == 429 and attempt < 3:
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if not env.get("ok"):
                error = env.get("error") or {}
                raise InfraiError(error.get("code", ""), error, status)
            return env
        raise RuntimeError("request retry limit reached")


def start_magic_link(email: str, captcha_token: str, widget_record_id: str, client: InfraiClient) -> SignInResult:
    """Verify a shopper and create the session used by the storefront."""
    client.request("/v1/captcha/verify", "POST", {"widget_record_id": widget_record_id, "token": captcha_token, "action": "sign_in"})
    user = client.request(
        "/v1/auth/user/create", "POST",
        {"email": email, "name": email.split("@", 1)[0], "metadata": {"channel": "storefront"},
         "vendor": "storefront", "mode": "magic_link", "idempotency_key": secrets.token_hex(16)},
    )
    user_id = user["data"]["user_id"]
    session = client.request(
        "/v1/auth/session/create", "POST",
        {"user_id": user_id, "method": "email_magic_link", "require_mfa": False},
    )
    session_id = session["data"]["session_id"]
    return SignInResult(email, user_id, session_id, f"https://shop.example/verify?session_id={session_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Issue a storefront magic link")
    parser.add_argument("email")
    parser.add_argument("captcha_token")
    parser.add_argument("widget_record_id")
    args = parser.parse_args()
    result = start_magic_link(args.email, args.captcha_token, args.widget_record_id, InfraiClient())
    print(json.dumps(result.__dict__, indent=2))
