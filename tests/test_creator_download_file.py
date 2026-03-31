import asyncio
import hashlib
import os
from types import SimpleNamespace

import requests

import kemonodownloader.creator_downloader as cd
from kemonodownloader.creator_downloader import CreatorDownloadThread


class DummyLogger:
    def emit(self, *args, **kwargs):
        return None


def test_download_file_skips_if_in_hashdb(tmp_path):
    file_url = "https://kemono.cr/files/1.jpg"
    other_files_dir = str(tmp_path / "hashdb")
    existing_path = str(tmp_path / "existing.jpg")
    data = b"hello"
    with open(existing_path, "wb") as fh:
        fh.write(data)

    expected_hash = hashlib.md5(data).hexdigest()
    expected_size = len(data)
    url_hash = hashlib.md5(file_url.encode()).hexdigest()

    thread = CreatorDownloadThread(
        "svc",
        "cid",
        str(tmp_path / "downloads"),
        ["p1"],
        [file_url],
        {file_url: "p1"},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(file_download_max_retries=1, settings_tab=None),
    )
    thread.log = DummyLogger()

    # Monkeypatch lookup to report existing file
    def fake_lookup(u_hash):
        if u_hash == url_hash:
            return {
                "file_path": existing_path,
                "file_hash": expected_hash,
                "file_size": expected_size,
            }
        return None

    thread.hash_db.lookup = fake_lookup

    calls = []

    def _safe_emit(signal, *args):
        calls.append(args)

    thread._safe_emit = _safe_emit

    asyncio.run(thread.download_file(file_url, str(tmp_path / "out"), 0, 1))

    # Expect file_progress emit with 100 and file_completed True
    assert any(args == (0, 100) for args in calls)
    assert any(args == (0, file_url, True) for args in calls)


def test_download_file_downloads_and_stores_hash(tmp_path, monkeypatch):
    file_url = "https://kemono.cr/files/2.jpg"
    other_files_dir = str(tmp_path / "hashdb")
    download_folder = str(tmp_path / "out")
    post_id = "p2"

    # Prepare a dummy streaming response
    class DummyResponse:
        def __init__(self, data: bytes):
            self._data = data
            self.headers = {"content-length": str(len(data))}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=8192):
            yield self._data

        def close(self):
            return None

    class DummySession:
        def get(self, *args, **kwargs):
            return DummyResponse(b"world")

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: DummySession())

    thread = CreatorDownloadThread(
        "svc",
        "cid",
        download_folder,
        [post_id],
        [file_url],
        {file_url: post_id},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(file_download_max_retries=1, settings_tab=None),
    )
    thread.log = DummyLogger()

    calls = []

    def _safe_emit(signal, *args):
        calls.append(args)

    thread._safe_emit = _safe_emit

    # Compute expected target path via generator
    target_folder, filename = thread.generate_filename_and_folder(
        file_url, download_folder, 0, 1, post_id, "Title"
    )
    expected_path = os.path.join(target_folder, filename.replace("/", "_"))

    asyncio.run(thread.download_file(file_url, download_folder, 0, 1))

    assert os.path.exists(expected_path)

    # Hash DB should now contain an entry for the URL
    url_hash = hashlib.md5(file_url.encode()).hexdigest()
    entry = thread.hash_db.lookup(url_hash)
    assert entry is not None
    assert entry["file_path"] == expected_path


def test_download_file_size_mismatch_marks_failed_and_removes_incomplete(
    tmp_path, monkeypatch
):
    file_url = "https://kemono.cr/files/3.jpg"
    other_files_dir = str(tmp_path / "hashdb")
    download_folder = str(tmp_path / "out")
    post_id = "p3"

    class DummyResponse:
        def __init__(self):
            # claim larger size than actually sent
            self.headers = {"content-length": "10"}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=8192):
            yield b"abc"

        def close(self):
            return None

    class DummySession:
        def get(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: DummySession())

    thread = CreatorDownloadThread(
        "svc",
        "cid",
        download_folder,
        [post_id],
        [file_url],
        {file_url: post_id},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(file_download_max_retries=1, settings_tab=None),
    )
    thread.log = DummyLogger()

    calls = []

    def _safe_emit(signal, *args):
        calls.append(args)

    thread._safe_emit = _safe_emit

    asyncio.run(thread.download_file(file_url, download_folder, 0, 1))

    # Should have been marked failed
    assert file_url in thread.failed_files
    # Incomplete file should not exist
    target_folder, filename = thread.generate_filename_and_folder(
        file_url, download_folder, 0, 1, post_id, "Title"
    )
    full_path = os.path.join(target_folder, filename.replace("/", "_"))
    assert not os.path.exists(full_path)


def test_download_file_retries_and_succeeds(monkeypatch, tmp_path):
    file_url = "https://kemono.cr/files/4.jpg"
    other_files_dir = str(tmp_path / "hashdb")
    download_folder = str(tmp_path / "out")
    post_id = "p4"

    attempts = {"count": 0}

    class DummyResponse:
        def __init__(self, data: bytes):
            self._data = data
            self.headers = {"content-length": str(len(data))}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=8192):
            yield self._data

        def close(self):
            return None

    class DummySession:
        def get(self, *args, **kwargs):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise requests.RequestException("temporary")
            return DummyResponse(b"ok")

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: DummySession())

    # Patch sleep to avoid waiting
    async def _no_sleep(_):
        return None

    monkeypatch.setattr(cd.asyncio, "sleep", _no_sleep)

    thread = CreatorDownloadThread(
        "svc",
        "cid",
        download_folder,
        [post_id],
        [file_url],
        {file_url: post_id},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(file_download_max_retries=2, settings_tab=None),
    )
    thread.log = DummyLogger()

    calls = []

    def _safe_emit(signal, *args):
        calls.append(args)

    thread._safe_emit = _safe_emit

    asyncio.run(thread.download_file(file_url, download_folder, 0, 1))

    # Should have attempted at least twice and succeeded
    assert attempts["count"] >= 2
    # File should exist now
    target_folder, filename = thread.generate_filename_and_folder(
        file_url, download_folder, 0, 1, post_id, "Title"
    )
    full_path = os.path.join(target_folder, filename.replace("/", "_"))
    assert os.path.exists(full_path)
