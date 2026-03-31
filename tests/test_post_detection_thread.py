import gzip
import json
from types import SimpleNamespace

import kemonodownloader.creator_downloader as cd
from kemonodownloader.creator_downloader import PostDetectionThread


class DummyLogger:
    def emit(self, *args, **kwargs):
        return None


class DummySignal:
    def __init__(self):
        self.last = None

    def emit(self, value):
        self.last = value


def _make_dummy_session(response):
    class DummySession:
        def get(self, *args, **kwargs):
            return response

    return DummySession()


def test_post_detection_gzipped_json_list(monkeypatch):
    posts = [
        {
            "id": "42",
            "title": "Hello",
            "file": {"path": "/files/1.jpg", "name": "a.jpg"},
        }
    ]
    data = json.dumps(posts).encode("utf-8")
    gz = gzip.compress(data)

    class DummyResponse:
        status_code = 200

        def __init__(self, content):
            self.content = content

    resp = DummyResponse(gz)
    monkeypatch.setattr(
        cd, "get_session", lambda settings_tab: _make_dummy_session(resp)
    )

    finished = DummySignal()
    thread = PostDetectionThread(
        "https://kemono.cr/fanbox/user/12345",
        {},
        SimpleNamespace(creator_posts_max_attempts=1, settings_tab=None),
    )
    thread.log = DummyLogger()
    thread.finished = finished

    thread.run()

    assert finished.last is not None
    assert isinstance(finished.last, list)
    assert finished.last[0][0] == "Hello"


def test_post_detection_json_with_posts_key(monkeypatch):
    posts = {
        "posts": [
            {
                "id": "99",
                "title": "Title99",
                "file": {"path": "/img/x.png", "name": "x.png"},
            }
        ]
    }
    data = json.dumps(posts).encode("utf-8")

    class DummyResponse:
        status_code = 200

        def __init__(self, content):
            self.content = content

        @property
        def text(self):
            return self.content.decode("utf-8")

    resp = DummyResponse(data)
    monkeypatch.setattr(
        cd, "get_session", lambda settings_tab: _make_dummy_session(resp)
    )

    finished = DummySignal()
    thread = PostDetectionThread(
        "https://kemono.cr/fanbox/user/000",
        {},
        SimpleNamespace(creator_posts_max_attempts=1, settings_tab=None),
    )
    thread.log = DummyLogger()
    thread.finished = finished

    thread.run()

    assert finished.last is not None
    assert finished.last[0][0] == "Title99"
