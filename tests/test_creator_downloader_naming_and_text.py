import os
from types import SimpleNamespace

from kemonodownloader import creator_downloader as cd


def make_thread(tmp_path, template=None, strategy=None, auto_rename=True):
    download_folder = str(tmp_path / "dl")
    other_files = str(tmp_path / "other")
    os.makedirs(download_folder, exist_ok=True)
    os.makedirs(other_files, exist_ok=True)

    settings_tab = SimpleNamespace()
    settings_tab.get_creator_filename_template = lambda: template
    settings_tab.get_creator_folder_strategy = lambda: strategy
    # Provide other settings used by ThreadSettings if accessed
    settings_tab.get_creator_posts_max_attempts = lambda: 1
    settings_tab.get_post_data_max_retries = lambda: 1
    settings_tab.get_file_download_max_retries = lambda: 1
    settings_tab.get_api_request_max_retries = lambda: 1
    settings_tab.get_simultaneous_downloads = lambda: 1

    # Create a ThreadSettings object expected by CreatorDownloadThread
    settings = cd.ThreadSettings(
        creator_posts_max_attempts=1,
        post_data_max_retries=1,
        file_download_max_retries=1,
        api_request_max_retries=1,
        simultaneous_downloads=1,
        settings_tab=settings_tab,
    )

    files = [
        "https://kemono.cr/files/path/origname.jpg?f=origname.jpg",
        "https://kemono.cr/files/path/other.png",
    ]
    files_map = {files[0]: "p1", files[1]: "p1"}
    post_titles_map = {("kemono", "1", "p1"): "My Post Title"}

    thread = cd.CreatorDownloadThread(
        "kemono",
        "1",
        download_folder,
        ["p1"],
        files,
        files_map,
        None,
        other_files,
        post_titles_map,
        auto_rename,
        settings,
        1,
        download_text=False,
    )
    return thread


def test_generate_filename_and_folder_default(tmp_path):
    thread = make_thread(tmp_path, template=None, strategy=None, auto_rename=True)

    # First file: should apply auto-rename prefix 1_
    target_folder, filename = thread.generate_filename_and_folder(
        thread.files_to_download[0], str(tmp_path / "dl"), 0, 2, "p1", "My Post"
    )

    assert filename.endswith(".jpg")
    assert filename.startswith("1_")
    # Default strategy is per_post -> folder contains post id and sanitized title
    assert os.path.basename(target_folder).startswith("p1_")

    # Second file for same post should increment counter
    _, filename2 = thread.generate_filename_and_folder(
        thread.files_to_download[1], str(tmp_path / "dl"), 1, 2, "p1", "My Post"
    )
    assert filename2.startswith("2_")


def test_get_desc_folder_for_post_strategies(tmp_path):
    # per_post
    thread = make_thread(tmp_path, strategy="per_post")
    # get_desc_folder_for_post expects the creator_folder (download root + creator folder)
    creator_folder = os.path.join(str(tmp_path / "dl"), "1_1")
    desc = thread.get_desc_folder_for_post(creator_folder, "p1", "T1")
    assert desc.endswith(os.path.join("1_1", "p1_T1"))

    # single_folder
    thread = make_thread(tmp_path, strategy="single_folder")
    creator_folder = os.path.join(str(tmp_path / "dl"), "1_1")
    desc = thread.get_desc_folder_for_post(creator_folder, "p1", "T1")
    assert os.path.normpath(desc) == os.path.normpath(creator_folder)

    # by_file_type
    thread = make_thread(tmp_path, strategy="by_file_type")
    creator_folder = os.path.join(str(tmp_path / "dl"), "1_1")
    desc = thread.get_desc_folder_for_post(creator_folder, "p1", "T1")
    assert desc.endswith(os.path.join("1_1", "txt"))


def test__download_text_sync_writes_file(monkeypatch, tmp_path):
    thread = make_thread(tmp_path)

    class FakeResp:
        status_code = 200

        def json(self):
            return {"post": {"content": "<p>Hello world</p>"}}

    class FakeSession:
        def get(self, *a, **k):
            return FakeResp()

    monkeypatch.setattr(cd, "get_session", lambda settings_tab=None: FakeSession())

    post_folder = str(tmp_path / "dl" / "1_1" / "p1_My_Post_Title")
    os.makedirs(post_folder, exist_ok=True)

    # Ensure no desc file exists initially
    desc_path = os.path.join(post_folder, "desc_p1.txt")
    if os.path.exists(desc_path):
        os.remove(desc_path)

    # Call the sync writer directly
    thread._download_text_sync("p1", post_folder)

    assert os.path.exists(desc_path)
    with open(desc_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    assert "Hello world" in content


def test_post_detection_thread_invalid_url_emits_error():
    errors = []
    settings = SimpleNamespace(
        creator_posts_max_attempts=1, settings_tab=SimpleNamespace()
    )
    # URL with insufficient path parts -> should emit error
    thread = cd.PostDetectionThread("https://kemono.cr/invalid", {}, settings)
    thread.error = SimpleNamespace(emit=lambda msg: errors.append(msg))
    thread.log = SimpleNamespace(emit=lambda *a, **k: None)
    thread.run()
    assert errors, "Expected error to be emitted for invalid URL"


def test_post_detection_thread_successful_parsing(monkeypatch):
    posts_emitted = []
    finished = []

    settings = SimpleNamespace(
        creator_posts_max_attempts=1, settings_tab=SimpleNamespace()
    )

    # Fake response: a JSON array of posts
    class FakeResp:
        status_code = 200

        def __init__(self, data):
            self.content = data.encode()
            self.text = data

    class FakeSession:
        def get(self, *a, **k):
            return FakeResp('[{"id": "10", "title": "T1", "file": {"path": "/f.jpg"}}]')

    monkeypatch.setattr(cd, "get_session", lambda settings_tab=None: FakeSession())

    url = "https://kemono.cr/fanbox/user/1"
    thread = cd.PostDetectionThread(url, {}, settings)
    thread.posts_batch = SimpleNamespace(emit=lambda batch: posts_emitted.append(batch))
    thread.finished = SimpleNamespace(emit=lambda data: finished.append(data))
    thread.log = SimpleNamespace(emit=lambda *a, **k: None)
    thread.run()

    # Expect at least one batch and final finished list
    assert posts_emitted or finished


def test_download_file_short_circuits_when_hash_matches(tmp_path):
    thread = make_thread(tmp_path)

    file_url = thread.files_to_download[0]
    # Create an existing file and register it in the hash DB
    existing_path = os.path.join(str(tmp_path), "existing.bin")
    with open(existing_path, "wb") as fh:
        fh.write(b"abc")
    import hashlib

    file_hash = hashlib.md5(b"abc").hexdigest()
    file_size = os.path.getsize(existing_path)
    url_hash = hashlib.md5(file_url.encode()).hexdigest()
    thread.hash_db.store(url_hash, existing_path, file_hash, file_url, file_size)

    # Replace emitters to avoid Qt signals
    thread.file_progress = SimpleNamespace(emit=lambda *a, **k: None)
    thread.file_completed = SimpleNamespace(emit=lambda *a, **k: None)

    import asyncio

    asyncio.run(thread.download_file(file_url, str(tmp_path / "dl"), 0, 1))

    assert file_url in thread.completed_files


def test_download_file_makedirs_failure(monkeypatch, tmp_path):
    thread = make_thread(tmp_path)
    file_url = thread.files_to_download[0]

    # Make os.makedirs raise OSError to simulate filesystem permission error
    def raise_makedirs(path, exist_ok=False):
        raise OSError("no space")

    monkeypatch.setattr(cd.os, "makedirs", raise_makedirs)

    captured = []
    thread.file_completed = SimpleNamespace(
        emit=lambda idx, url, success: captured.append((idx, url, success))
    )

    import asyncio

    asyncio.run(thread.download_file(file_url, str(tmp_path / "dl"), 0, 1))

    assert file_url in thread.failed_files
    assert captured and captured[-1][2] is False


def test_download_file_size_mismatch_triggers_failure(monkeypatch, tmp_path):
    thread = make_thread(tmp_path)
    file_url = thread.files_to_download[0]

    class FakeResp:
        status_code = 200

        def __init__(self):
            self.headers = {"content-length": "10"}

        def raise_for_status(self):
            return

        def iter_content(self, chunk_size=8192):
            yield b"abcde"  # 5 bytes only

        def close(self):
            return

    class FakeSession:
        def get(self, *a, **k):
            return FakeResp()

    monkeypatch.setattr(cd, "get_session", lambda settings_tab=None: FakeSession())

    # Limit retries to 1 via the settings already provided by make_thread
    import asyncio

    asyncio.run(thread.download_file(file_url, str(tmp_path / "dl"), 0, 1))

    assert file_url in thread.failed_files


def test_download_file_request_exception_retries(monkeypatch, tmp_path):
    thread = make_thread(tmp_path)
    file_url = thread.files_to_download[0]

    import requests

    class FakeSession:
        def get(self, *a, **k):
            raise requests.RequestException("network fail")

    monkeypatch.setattr(cd, "get_session", lambda settings_tab=None: FakeSession())

    captured = []
    thread.file_completed = SimpleNamespace(
        emit=lambda idx, url, success: captured.append((idx, url, success))
    )

    import asyncio

    asyncio.run(thread.download_file(file_url, str(tmp_path / "dl"), 0, 1))

    assert file_url in thread.failed_files
    assert captured and captured[-1][2] is False


def test_cancellation_thread_signals_stop_and_finishes():
    class FakeT:
        def __init__(self):
            self.stopped = False
            self._running = True

        def stop(self):
            self.stopped = True
            self._running = False

        def isRunning(self):
            return self._running

    f = FakeT()
    canc = cd.CancellationThread([f])
    finished = []
    canc.finished = SimpleNamespace(emit=lambda: finished.append(True))
    logs = []
    canc.log = SimpleNamespace(emit=lambda *a, **k: logs.append(a))
    # Directly call run() to avoid QThread overhead
    canc.run()
    assert f.stopped
    assert finished


def test_generate_filename_template_fallback(tmp_path):
    thread = make_thread(
        tmp_path, template="{post_id:{bad}}", strategy=None, auto_rename=False
    )
    logs = []
    thread.log = SimpleNamespace(emit=lambda msg, level: logs.append((msg, level)))
    target_folder, filename = thread.generate_filename_and_folder(
        thread.files_to_download[0], str(tmp_path / "dl"), 0, 1, "p1", "My Post"
    )
    assert filename
    assert logs, "Expected a log warning when template formatting fails"


def test_fetch_creator_and_post_info_success(monkeypatch, tmp_path):
    thread = make_thread(tmp_path, template=None, strategy=None, auto_rename=False)
    # Ensure per-post titles are fetched by clearing map and using selected_posts
    thread.post_titles_map = {}
    thread.selected_posts = ["p1"]

    class FakeResp:
        def __init__(self, data, status_code=200):
            self._data = data
            self.status_code = status_code

        def json(self):
            return self._data

    class FakeSession:
        def get(self, url, *a, **k):
            if url.endswith("/profile"):
                return FakeResp({"name": "Creator Name"})
            elif "/post/" in url:
                return FakeResp({"title": "Fetched Title"})
            return FakeResp({}, 404)

    monkeypatch.setattr(cd, "get_session", lambda settings_tab=None: FakeSession())
    thread.fetch_creator_and_post_info()
    assert thread.creator_name == cd.sanitize_filename("Creator Name")
    key = ("kemono", "1", "p1")
    assert thread.post_titles_map.get(key) == cd.sanitize_filename("Fetched Title")


def test_download_worker_processes_queue(monkeypatch, tmp_path):
    thread = make_thread(tmp_path)
    processed = []

    async def fake_download(file_url, folder, file_index, total_files):
        processed.append(file_url)
        # mark as completed for completeness
        thread.completed_files.add(file_url)

    thread.download_file = fake_download

    import asyncio

    async def runner():
        q = asyncio.Queue()
        await q.put((0, thread.files_to_download[0]))
        task = asyncio.create_task(thread.download_worker(q, str(tmp_path / "dl"), 1))
        await asyncio.wait_for(q.join(), timeout=1.0)
        thread.is_running = False
        await asyncio.gather(task, return_exceptions=True)

    asyncio.run(runner())
    assert processed and processed[0] == thread.files_to_download[0]


def test_check_post_completion_emits_post_completed(tmp_path):
    thread = make_thread(tmp_path)
    file1, file2 = thread.files_to_download[0], thread.files_to_download[1]
    thread.post_files_map = {"p1": [file1, file2]}
    thread.completed_files = set([file1])
    collected = []
    thread.post_completed = SimpleNamespace(emit=lambda pid: collected.append(pid))
    thread.check_post_completion(file1)
    assert not collected
    thread.completed_files.add(file2)
    thread.check_post_completion(file2)
    assert collected == ["p1"]


def test_creator_download_thread_run_processes_all_files(monkeypatch, tmp_path):
    thread = make_thread(tmp_path)
    # Replace signal-like attributes to avoid Qt interactions
    thread.log = SimpleNamespace(emit=lambda *a, **k: None)
    thread.file_progress = SimpleNamespace(emit=lambda *a, **k: None)
    thread.file_completed = SimpleNamespace(emit=lambda *a, **k: None)
    thread.post_completed = SimpleNamespace(emit=lambda *a, **k: None)

    # Avoid network calls during fetch
    thread.fetch_creator_and_post_info = lambda: None

    # Async worker that simply consumes queue items and marks them completed
    import asyncio

    async def fake_worker(queue, folder, total_files):
        while True:
            try:
                file_index, file_url = await asyncio.wait_for(queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                break
            with thread.completed_files_lock:
                thread.completed_files.add(file_url)
            queue.task_done()

    # Install fake worker (no binding to self required)
    thread.download_worker = fake_worker

    # Run the thread's run() synchronously
    thread.run()

    # All files should have been processed
    assert set(thread.files_to_download).issubset(thread.completed_files)
