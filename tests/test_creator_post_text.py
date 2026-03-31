import os
from types import SimpleNamespace

import kemonodownloader.creator_downloader as cd
from kemonodownloader.creator_downloader import CreatorDownloadThread


class DummyLogger:
    def emit(self, *args, **kwargs):
        return None


def test__download_text_sync_writes_description_file(tmp_path, monkeypatch):
    # Arrange: patch get_session to return a dummy response with HTML content
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"content": "<p>Hello <strong>World</strong></p>"}

    class DummySession:
        def get(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: DummySession())

    service = "svc"
    creator_id = "cid"
    download_folder = str(tmp_path / "downloads")
    other_files_dir = str(tmp_path / "hashdb")

    thread = CreatorDownloadThread(
        service,
        creator_id,
        download_folder,
        [],
        [],
        {},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(settings_tab=None),
    )
    thread.log = DummyLogger()

    post_folder = str(tmp_path / "desc")
    os.makedirs(post_folder, exist_ok=True)

    # Act
    thread._download_text_sync("42", post_folder)

    # Assert
    desc_path = os.path.join(post_folder, "desc_42.txt")
    assert os.path.exists(desc_path)
    with open(desc_path, "r", encoding="utf-8") as fh:
        data = fh.read()
    assert "Hello" in data and "World" in data


def test__download_text_sync_skips_when_file_exists(tmp_path, monkeypatch):
    # Ensure that existing desc file prevents network calls
    called = {"hit": False}

    def _bad_get_session(_):
        called["hit"] = True
        raise AssertionError("Network should not be called when file exists")

    monkeypatch.setattr(cd, "get_session", _bad_get_session)

    service = "svc"
    creator_id = "cid"
    download_folder = str(tmp_path / "downloads")
    other_files_dir = str(tmp_path / "hashdb")

    thread = CreatorDownloadThread(
        service,
        creator_id,
        download_folder,
        [],
        [],
        {},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(settings_tab=None),
    )
    thread.log = DummyLogger()

    post_folder = str(tmp_path / "desc")
    os.makedirs(post_folder, exist_ok=True)
    desc_path = os.path.join(post_folder, "desc_42.txt")
    with open(desc_path, "w", encoding="utf-8") as fh:
        fh.write("existing")

    # Act: should not call network and should simply return
    thread._download_text_sync("42", post_folder)
    assert called["hit"] is False
    with open(desc_path, "r", encoding="utf-8") as fh:
        assert fh.read() == "existing"
