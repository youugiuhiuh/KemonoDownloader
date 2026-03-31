import time
from types import SimpleNamespace
from urllib.parse import urljoin

import kemonodownloader.creator_downloader as cd
from kemonodownloader.creator_downloader import FilePreparationThread


class DummyCheckbox:
    def __init__(self, checked: bool):
        self._checked = checked

    def isChecked(self):
        return self._checked


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json = json_data
        self.content = content

    def json(self):
        return self._json


def test_fetch_and_detect_files_success(monkeypatch):
    post_id = "123"
    file_path = "/files/10.png"
    post_obj = {"id": post_id, "file": {"path": file_path, "name": "orig.png"}}

    resp = DummyResponse(status_code=200, json_data=post_obj)

    class Session:
        def get(self, *a, **k):
            return resp

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: Session())

    ext_checks = {".png": DummyCheckbox(True)}
    settings = SimpleNamespace(post_data_max_retries=1, settings_tab=None)
    thread = FilePreparationThread(
        [post_id], {}, ext_checks, True, True, False, settings
    )
    thread.log = SimpleNamespace(emit=lambda *a, **k: None)

    result = thread.fetch_and_detect_files(post_id, "https://kemono.cr/fanbox/user/1")
    assert result is not None
    pid, files = result
    assert pid == post_id
    expected_url = urljoin("https://kemono.cr", file_path) + "?f=orig.png"
    assert files == [("orig.png", expected_url)]


def test_fetch_and_detect_files_handles_429_and_retries(monkeypatch):
    post_id = "555"
    file_path = "/files/x.jpg"
    post_obj = {"id": post_id, "file": {"path": file_path, "name": "x.jpg"}}

    calls = {"n": 0}

    class Session:
        def get(self, *a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                return DummyResponse(status_code=429, json_data=None)
            return DummyResponse(status_code=200, json_data=post_obj)

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: Session())
    # Avoid sleeping delays
    monkeypatch.setattr(time, "sleep", lambda s: None)

    ext_checks = {".jpg": DummyCheckbox(True)}
    settings = SimpleNamespace(post_data_max_retries=2, settings_tab=None)
    thread = FilePreparationThread(
        [post_id], {}, ext_checks, True, True, False, settings
    )
    thread.log = SimpleNamespace(emit=lambda *a, **k: None)

    result = thread.fetch_and_detect_files(post_id, "https://kemono.cr/fanbox/user/1")
    assert result is not None
    pid, files = result
    assert pid == post_id
    expected_url = urljoin("https://kemono.cr", file_path) + "?f=x.jpg"
    assert files == [("x.jpg", expected_url)]
