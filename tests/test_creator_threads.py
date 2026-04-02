from types import SimpleNamespace
from unittest.mock import MagicMock

import kemonodownloader.creator_downloader as cd


class FakeThread:
    def __init__(self, running=False):
        self._running = running
        self.stop_called = False

    def stop(self):
        self.stop_called = True
        self._running = False

    def isRunning(self):
        return self._running


def test_cancellation_thread_stops_and_finishes():
    t = FakeThread(running=False)
    ct = cd.CancellationThread([t])
    # run directly (not starting as QThread) to exercise run logic
    ct.run()
    assert t.stop_called


def test_checkbox_toggle_thread_updates_states():
    # visible_posts: list of (title, (post_id, ...))
    visible = [("post1", ("id1", None)), ("post2", ("id2", None))]
    checked = {"id1": False, "id2": False, "id3": True}

    # check_all_state: 2 == Checked, otherwise Unchecked
    thread = cd.CheckboxToggleThread(visible, checked, 2)
    # run directly to avoid QThread scheduling
    thread.run()

    # After running with check_all_state==2, visible ids should be True
    assert thread.checked_urls["id1"] is True
    assert thread.checked_urls["id2"] is True
    # Non-visible id should retain its original value
    assert thread.checked_urls["id3"] is True


def _mk_signal_mock():
    return SimpleNamespace(emit=MagicMock())


def test_post_population_thread_maps_posts(qapp):
    detected_posts = [("Title1", (1, "thumb1")), ("Title2", (2, "thumb2"))]
    t = cd.PostPopulationThread(detected_posts)
    t.finished = _mk_signal_mock()
    t.log = _mk_signal_mock()
    t.run()
    expected = {
        "Title1 (ID: 1)": (1, "thumb1"),
        "Title2 (ID: 2)": (2, "thumb2"),
    }
    t.finished.emit.assert_called_once_with(expected, detected_posts)


def test_filter_thread_runs(qapp):
    all_detected = [("First Post", (1, "u1")), ("Other", (2, "u2"))]
    checked = {1: True, 2: False}
    t = cd.FilterThread(all_detected, checked, "first")
    t.finished = _mk_signal_mock()
    t.log = _mk_signal_mock()
    t.run()
    filtered = [("First Post", 1, "u1", True)]
    t.finished.emit.assert_called_once_with(filtered)


def test_checkbox_toggle_thread(qapp):
    visible = [("A", (1, "u1")), ("B", (2, "u2"))]
    checked = {1: False, 2: False}
    t = cd.CheckboxToggleThread(visible, checked, 2)
    t.finished = _mk_signal_mock()
    t.log = _mk_signal_mock()
    t.run()
    # Inspect the emitted args
    assert t.finished.emit.called
    new_checked, posts_to_download = t.finished.emit.call_args[0]
    assert new_checked[1] is True and new_checked[2] is True
    assert set(posts_to_download) == {1, 2}


def test_validation_thread_invalid_url(qapp):
    settings = SimpleNamespace(api_request_max_retries=1, settings_tab=None)
    t = cd.ValidationThread("http://bad/url", settings)
    t.log = _mk_signal_mock()
    t.result = _mk_signal_mock()
    t.run()
    t.result.emit.assert_called_with(False)


def test_validation_thread_success(monkeypatch, qapp):
    settings = SimpleNamespace(api_request_max_retries=1, settings_tab=None)

    class Resp:
        status_code = 200

        @property
        def text(self):
            return "This page mentions kemono somewhere"

    class S:
        def get(self, url, headers=None, timeout=None):
            return Resp()

    monkeypatch.setattr(cd, "get_session", lambda st: S())
    t = cd.ValidationThread("https://kemono.cr/user/1", settings)
    t.log = _mk_signal_mock()
    t.result = _mk_signal_mock()
    t.run()
    t.result.emit.assert_called_with(True)
