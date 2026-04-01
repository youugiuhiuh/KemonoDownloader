from types import SimpleNamespace

from kemonodownloader import creator_downloader as cd


def make_parent(tmp_path):
    parent = SimpleNamespace()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    parent.download_folder = str(tmp_path / "dl")
    st = SimpleNamespace()
    st.settings_applied = SimpleNamespace(connect=lambda cb: None)
    st.language_changed = SimpleNamespace(connect=lambda cb: None)
    st.get_creator_posts_max_attempts = lambda: 1
    st.get_post_data_max_retries = lambda: 1
    st.get_file_download_max_retries = lambda: 1
    st.get_api_request_max_retries = lambda: 1
    st.get_simultaneous_downloads = lambda: 1
    parent.settings_tab = st
    parent.ensure_folders_exist = lambda: None
    parent.post_tab = SimpleNamespace()
    parent.creator_tab = SimpleNamespace()
    return parent


def test_detection_to_population_flow(tmp_path, monkeypatch):
    parent = make_parent(tmp_path)
    tab = cd.CreatorDownloaderTab(parent)

    class FakeSignal:
        def __init__(self):
            self.cb = None

        def connect(self, cb):
            self.cb = cb

        def emit(self, *args):
            if self.cb:
                # Call only as many args as the slot accepts to mimic Qt behavior
                import inspect

                try:
                    n = len(inspect.signature(self.cb).parameters)
                except Exception:
                    n = 0
                self.cb(*args[:n])

    class FakePostDetectionThread:
        def __init__(self, url, post_titles_map, settings):
            self.finished = FakeSignal()
            self.posts_batch = FakeSignal()
            self.log = FakeSignal()
            self.error = FakeSignal()

        def isRunning(self):
            return False

        def start(self):
            batch = [("T1", ("p1", "thumb1"))]
            self.posts_batch.emit(batch)
            self.finished.emit(batch)

    class FakePostPopulationThread:
        def __init__(self, detected_posts):
            self.finished = FakeSignal()
            self.log = FakeSignal()

        def isRunning(self):
            return False

        def start(self):
            post_url_map = {"T1 (ID: p1)": ("p1", "thumb1")}
            self.finished.emit(post_url_map, [("T1", ("p1", "thumb1"))])

    monkeypatch.setattr(cd, "PostDetectionThread", FakePostDetectionThread)
    monkeypatch.setattr(cd, "PostPopulationThread", FakePostPopulationThread)

    url = "https://kemono.cr/fanbox/user/1"
    tab.creator_queue.append((url, False))
    tab.update_creator_queue_list()

    # Trigger the check which will use our fake threads synchronously
    tab.check_creator_from_queue(url)

    assert tab.all_detected_posts
    assert tab.post_url_map
    # Ensure items are added to checked_urls for new posts
    assert any(pid in tab.checked_urls for _, (pid, _) in tab.all_detected_posts)
