"""Unit tests for memcli.gateway."""
from __future__ import annotations

import json
from io import BytesIO
from unittest import mock

import pytest

from memcli import gateway


def _make_response(body: dict | str, status: int = 200):
    """Build a mock urllib response object."""
    raw = json.dumps(body).encode() if isinstance(body, dict) else body.encode()
    resp = mock.MagicMock()
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = mock.MagicMock(return_value=False)
    return resp


def test_post_json_success():
    payload = {"tool": "llm-task", "args": {}}
    response_body = {"result": {"content": [{"type": "text", "text": "{}"}]}}

    with mock.patch("urllib.request.urlopen", return_value=_make_response(response_body)):
        result = gateway.post_json("http://localhost/tools/invoke", payload)

    assert result == response_body


def test_post_json_sends_bearer_token():
    captured_request = []

    def fake_urlopen(req, timeout=None):
        captured_request.append(req)
        return _make_response({"ok": True})

    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        gateway.post_json("http://localhost/", {}, token="my-secret")

    req = captured_request[0]
    assert req.get_header("Authorization") == "Bearer my-secret"


def test_post_json_no_auth_header_when_no_token():
    captured_request = []

    def fake_urlopen(req, timeout=None):
        captured_request.append(req)
        return _make_response({})

    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        gateway.post_json("http://localhost/", {})

    req = captured_request[0]
    assert req.get_header("Authorization") is None


def test_post_json_http_error_raises_runtime_error():
    import urllib.error

    err = urllib.error.HTTPError(
        url="http://localhost/",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=BytesIO(b"server exploded"),
    )
    with mock.patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(RuntimeError, match="Gateway HTTP 500"):
            gateway.post_json("http://localhost/", {})


def test_post_json_url_error_raises_runtime_error():
    import urllib.error

    err = urllib.error.URLError(reason="connection refused")
    with mock.patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(RuntimeError, match="Gateway request failed"):
            gateway.post_json("http://localhost/", {})


def test_post_json_invalid_json_response_raises_runtime_error():
    resp = mock.MagicMock()
    resp.read.return_value = b"not json {"
    resp.__enter__ = lambda s: s
    resp.__exit__ = mock.MagicMock(return_value=False)

    with mock.patch("urllib.request.urlopen", return_value=resp):
        with pytest.raises(RuntimeError, match="invalid JSON"):
            gateway.post_json("http://localhost/", {})


def test_post_json_sends_content_type_header():
    captured = []

    def fake_urlopen(req, timeout=None):
        captured.append(req)
        return _make_response({})

    with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
        gateway.post_json("http://localhost/", {"key": "val"})

    assert captured[0].get_header("Content-type") == "application/json"
