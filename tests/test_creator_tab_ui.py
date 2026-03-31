import os

from PyQt6.QtWidgets import QWidget

from kemonodownloader.creator_downloader import CreatorDownloaderTab


def test_creator_tab_ui_and_fast_mode(tmp_path):
    parent = QWidget()
    # Provide required folder attributes
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")

    tab = CreatorDownloaderTab(parent)
    # Make parent visible so visibility checks behave predictably
    parent.show()
    tab.show()

    # Directories should be created
    assert os.path.exists(parent.cache_folder)
    assert os.path.exists(parent.other_files_folder)

    # Fast mode toggles visibility of multi-url input
    tab.toggle_fast_mode(2)  # checked
    assert tab.creator_multi_url_input.isVisible()

    tab.toggle_fast_mode(0)  # unchecked
    assert not tab.creator_multi_url_input.isVisible()


def test_add_multiple_creators_to_queue_valid_and_invalid(tmp_path):
    parent = QWidget()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    tab = CreatorDownloaderTab(parent)

    # Provide one valid and one invalid URL
    tab.creator_multi_url_input.setPlainText(
        "https://kemono.cr/fanbox/user/123\nhttps://example.com/bad/url"
    )
    tab.add_multiple_creators_to_queue()

    # Only the valid kemono.cr URL should be added
    assert any("kemono.cr" in u for u, _ in tab.creator_queue)
