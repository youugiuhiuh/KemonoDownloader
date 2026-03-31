from PyQt6.QtWidgets import QMessageBox, QWidget

from kemonodownloader.creator_downloader import CreatorDownloaderTab


def test_add_creators_from_file_and_valid_url(tmp_path, monkeypatch):
    file_path = tmp_path / "links.txt"
    file_path.write_text("https://kemono.cr/fanbox/user/111\nhttps://example.com/bad\n")

    parent = QWidget()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    tab = CreatorDownloaderTab(parent)

    # Monkeypatch file dialog to return our file
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QFileDialog.getOpenFileName",
        lambda *a, **k: (str(file_path), "Text Files (*.txt)"),
    )

    tab.add_creators_from_file()

    # Only the kemono.cr URL should be added
    assert any("kemono.cr" in u for u, _ in tab.creator_queue)


def test_create_remove_handler_removes_url(monkeypatch):
    parent = QWidget()
    parent.cache_folder = "/tmp/cache"
    parent.other_files_folder = "/tmp/other"
    tab = CreatorDownloaderTab(parent)

    url = "https://kemono.cr/fanbox/user/222"
    tab.creator_queue = [(url, False)]

    # Simulate user clicking Yes in the confirmation dialog
    monkeypatch.setattr(
        "PyQt6.QtWidgets.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    handler = tab.create_remove_handler(url)
    handler()

    assert not any(item[0] == url for item in tab.creator_queue)
