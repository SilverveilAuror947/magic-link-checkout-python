import pytest

from src.magic_link_service import InfraiClient, InfraiError, start_magic_link


class StubClient(InfraiClient):
    def __init__(self):
        self.calls = []
        self.api_key = "test"
        self.base_url = "https://example.invalid"

    def request(self, path, method, body=None):
        self.calls.append((path, method, body))
        if path.endswith("captcha/verify"):
            return {"ok": True, "data": {}}
        if path.endswith("user/create"):
            return {"ok": True, "data": {"user_id": "u_123"}}
        return {"ok": True, "data": {"session_id": "s_456"}}


def test_magic_link_connects_captcha_user_and_session():
    client = StubClient()
    result = start_magic_link("buyer@example.com", "captcha-ok", "widget-123", client)
    assert result.magic_link.endswith("session_id=s_456")
    assert [call[:2] for call in client.calls] == [
        ("/v1/captcha/verify", "POST"),
        ("/v1/auth/user/create", "POST"),
        ("/v1/auth/session/create", "POST"),
    ]
    assert client.calls[2][2]["user_id"] == "u_123"
    assert client.calls[0][2] == {"widget_record_id": "widget-123", "token": "captcha-ok", "action": "sign_in"}
