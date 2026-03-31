from types import SimpleNamespace

import kemonodownloader.creator_downloader as cd
from kemonodownloader.creator_downloader import (
    CheckboxToggleThread,
    FilterThread,
    LogsWindow,
    PostPopulationThread,
    ValidationThread,
)


class DummyLogger:
    def emit(self, *args, **kwargs):
        return None


class DummySignal:
    def __init__(self):
        self.args = None

    def emit(self, *args):
        self.args = args


def test_validation_thread_success(monkeypatch):
    # Return a response whose text contains the domain_check
    class Resp:
        status_code = 200

        def __init__(self):
            self.text = "Welcome to kemono"

    class Session:
        def get(self, *a, **k):
            return Resp()

    monkeypatch.setattr(cd, "get_session", lambda settings_tab: Session())
    settings = SimpleNamespace(api_request_max_retries=1, settings_tab=None)
    thread = ValidationThread("https://kemono.cr/fanbox/user/1", settings)
    thread.result = DummySignal()
    thread.log = DummyLogger()
    thread.run()
    assert thread.result.args is not None and thread.result.args[0] is True


def test_validation_thread_invalid_format():
    settings = SimpleNamespace(api_request_max_retries=1, settings_tab=None)
    thread = ValidationThread("https://example.com/not/a/user/url", settings)
    thread.result = DummySignal()
    thread.log = DummyLogger()
    thread.run()
    assert thread.result.args is not None and thread.result.args[0] is False


def test_post_population_thread_maps_titles(monkeypatch):
    detected = [("T1", ("p1", "u1")), ("T2", ("p2", "u2"))]
    thread = PostPopulationThread(detected)
    thread.log = DummyLogger()
    finished = DummySignal()
    thread.finished = finished
    thread.run()
    assert finished.args is not None
    post_map, posts = finished.args
    assert len(post_map) == 2
    assert any("T1" in k for k in post_map.keys())


def test_filter_thread_filters_and_emits():
    items = [("Hello", ("p1", "u1")), ("SearchMe", ("p2", "u2"))]
    checked = {"p1": True}
    thread = FilterThread(items, checked, "search")
    thread.log = DummyLogger()
    finished = DummySignal()
    thread.finished = finished
    thread.run()
    assert finished.args is not None
    filtered = finished.args[0]
    # Only SearchMe should match
    assert any("SearchMe" in it[0] for it in filtered)


def test_checkbox_toggle_thread_checks_and_emits():
    visible = [("A", ("p1", "u1")), ("B", ("p2", "u2"))]
    checked = {"p1": False, "p2": False}
    # set check_all_state to Qt.Checked (2)
    thread = CheckboxToggleThread(visible, checked, 2)
    thread.log = DummyLogger()
    finished = DummySignal()
    thread.finished = finished
    thread.run()
    assert finished.args is not None
    new_checked, posts_to_download = finished.args
    assert new_checked.get("p1") is True
    assert "p1" in posts_to_download or "p2" in posts_to_download


def test_logs_window_clear_and_download(tmp_path, monkeypatch):
    class Parent:
        def __init__(self):
            self.creator_console = SimpleNamespace(
                toHtml=lambda: "<p>LOG</p>", clear=lambda: None
            )
            self.appended = []

        def append_log_to_console(self, msg, level):
            self.appended.append((msg, level))

    parent = Parent()
    lw = LogsWindow(None)
    lw._parent = parent
    # Force update
    lw.needs_update = True
    lw._do_update()
    # Clear logs
    lw.clear_logs()
    assert lw.logs_display.toPlainText() == ""

    # Re-populate display so download_logs writes a file
    lw.logs_display.setPlainText("LINE1\nLINE2")

    # Monkeypatch QFileDialog.getSaveFileName to return a path
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(tmp_path / "logs.txt"), ""),
    )
    lw.download_logs()
    out_path = tmp_path / "logs.txt"
    assert out_path.exists()
    assert parent.appended, "Parent should have been notified of saved logs"
