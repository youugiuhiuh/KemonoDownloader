from PyQt6.QtWidgets import QWidget

from kemonodownloader.creator_downloader import CreatorDownloaderTab


def test_set_fetching_and_downloading_ui_state(tmp_path):
    parent = QWidget()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    tab = CreatorDownloaderTab(parent)

    # Fetching state disables download button and enables cancel
    tab.set_fetching_ui_state(True)
    assert not tab.creator_download_btn.isEnabled()
    assert tab.creator_cancel_btn.isEnabled()

    tab.set_fetching_ui_state(False)
    assert tab.creator_download_btn.isEnabled()

    # Downloading state locks most controls
    tab.set_downloading_ui_state(True)
    assert not tab.creator_download_btn.isEnabled()
    assert tab.creator_cancel_btn.isEnabled()

    tab.set_downloading_ui_state(False)
    assert tab.creator_download_btn.isEnabled()
