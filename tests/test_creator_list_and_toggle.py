from PyQt6.QtWidgets import QWidget

from kemonodownloader.creator_downloader import CreatorDownloaderTab


def test_add_list_item_creates_widget(tmp_path):
    parent = QWidget()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    tab = CreatorDownloaderTab(parent)

    text = "My Post (ID: p1)"
    tab.post_url_map[text] = ("p1", "thumb")

    assert tab.creator_post_list.count() == 0
    tab.add_list_item(text, "https://kemono.cr/post/1", is_checked=False)

    assert tab.creator_post_list.count() == 1
    assert text in tab.post_widget_cache
    item, widget = tab.post_widget_cache[text]
    assert hasattr(widget, "label") and widget.label.text() == text


def test_toggle_checkbox_state_updates_checked_urls(tmp_path):
    parent = QWidget()
    parent.cache_folder = str(tmp_path / "cache")
    parent.other_files_folder = str(tmp_path / "other")
    tab = CreatorDownloaderTab(parent)

    text = "PostTitle (ID: p2)"
    tab.post_url_map[text] = ("p2", "thumb")
    tab.add_list_item(text, "https://kemono.cr/post/2", is_checked=False)

    assert tab.checked_urls.get("p2") is None or tab.checked_urls["p2"] is False
    tab.toggle_checkbox_state(text)
    assert tab.checked_urls.get("p2") is True
