import asyncio
from types import SimpleNamespace

from kemonodownloader.creator_downloader import CreatorDownloadThread


class DummyLogger:
    def emit(self, *args, **kwargs):
        return None


class DummySignal:
    def __init__(self):
        self.args = None

    def emit(self, *args):
        self.args = args


def make_thread():
    return CreatorDownloadThread(
        "svc",
        "cid",
        "/tmp",
        ["p1"],
        ["url1", "url2"],
        {"url1": "p1", "url2": "p1"},
        None,
        "/tmp/hash",
        {},
        auto_rename_enabled=False,
        settings=SimpleNamespace(file_download_max_retries=1, settings_tab=None),
    )


def test_check_post_completion_emits_when_all_files_done():
    thread = make_thread()
    thread.log = DummyLogger()
    thread.post_completed = DummySignal()
    # both files in post_files_map
    thread.post_files_map = {"p1": ["url1", "url2"]}
    thread.completed_files = set(["url1", "url2"])
    thread.check_post_completion("url1")
    assert thread.post_completed.args is not None
    assert thread.post_completed.args[0] == "p1"


def test_check_post_completion_no_emit_if_not_complete():
    thread = make_thread()
    thread.log = DummyLogger()
    thread.post_completed = DummySignal()
    thread.post_files_map = {"p1": ["url1", "url2"]}
    thread.completed_files = set(["url1"])
    thread.check_post_completion("url1")
    assert thread.post_completed.args is None


def test_download_worker_calls_download_file(tmp_path):
    thread = make_thread()
    thread.log = DummyLogger()
    called = []

    async def fake_download(file_url, folder, file_index, total_files):
        called.append((file_url, folder, file_index, total_files))

    thread.download_file = fake_download
    thread.is_running = True

    async def runner():
        q = asyncio.Queue()
        await q.put((0, "url1"))
        t = asyncio.create_task(thread.download_worker(q, str(tmp_path), 1))
        await q.join()
        t.cancel()
        await asyncio.gather(t, return_exceptions=True)

    asyncio.run(runner())
    assert called and called[0][0] == "url1"
