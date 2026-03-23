import json
from unittest.mock import MagicMock


def _make_response(body: dict | list, status: int = 200):
    raw = json.dumps(body).encode()
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = raw
    mock.status = status
    return mock
