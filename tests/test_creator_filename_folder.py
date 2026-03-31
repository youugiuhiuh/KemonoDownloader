import os
from types import SimpleNamespace

from kemonodownloader.creator_downloader import CreatorDownloadThread


class DummySettingsTab:
    def __init__(self, strategy="per_post", template=None):
        self._strategy = strategy
        self._template = template

    def get_creator_folder_strategy(self):
        return self._strategy

    def get_creator_filename_template(self):
        return self._template


def test_generate_filename_and_folder_defaults_and_per_post(tmp_path):
    service = "svc"
    creator_id = "cid"
    download_folder = str(tmp_path / "downloads")
    other_files_dir = str(tmp_path / "hashdb")
    file_url = "https://kemono.cr/files/1.jpg?f=orig.jpg"

    post_id = "p1"
    post_title = "My Title"

    post_titles_map = {(service, creator_id, post_id): post_title}

    thread = CreatorDownloadThread(
        service,
        creator_id,
        download_folder,
        [post_id],
        [file_url],
        {file_url: post_id},
        None,
        other_files_dir,
        post_titles_map,
        auto_rename_enabled=False,
        settings=None,
    )

    target_folder, filename = thread.generate_filename_and_folder(
        file_url, download_folder, 0, 1, post_id, post_title
    )

    # Creator folder uses creator id twice when creator_name is None
    creator_folder_name = f"{creator_id}_{creator_id}"
    expected_folder = os.path.join(
        download_folder, creator_folder_name, f"{post_id}_My_Title"
    )
    assert os.path.normpath(target_folder) == os.path.normpath(expected_folder)
    assert filename == "p1_orig.jpg"


def test_generate_filename_and_folder_with_auto_rename(tmp_path):
    service = "svc"
    creator_id = "cid"
    download_folder = str(tmp_path / "downloads")
    other_files_dir = str(tmp_path / "hashdb")
    file_url = "https://kemono.cr/files/1.jpg?f=orig.jpg"

    post_id = "p1"
    post_title = "Title"

    thread = CreatorDownloadThread(
        service,
        creator_id,
        download_folder,
        [post_id],
        [file_url],
        {file_url: post_id},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=True,
        settings=None,
    )

    # First generated filename should have a prefix '1_'
    _, filename1 = thread.generate_filename_and_folder(
        file_url, download_folder, 0, 1, post_id, post_title
    )
    assert filename1.startswith("1_") and filename1.endswith(".jpg")


def test_get_desc_folder_for_post_strategies(tmp_path):
    service = "svc"
    creator_id = "cid"
    download_folder = str(tmp_path / "downloads")
    other_files_dir = str(tmp_path / "hashdb")

    settings = SimpleNamespace(settings_tab=DummySettingsTab(strategy="by_file_type"))
    thread = CreatorDownloadThread(
        service,
        creator_id,
        download_folder,
        [],
        [],
        {},
        None,
        other_files_dir,
        {},
        auto_rename_enabled=False,
        settings=settings,
    )

    df = thread.get_desc_folder_for_post(download_folder, "p1", "Title")
    assert df.endswith(os.path.join("downloads", "txt"))

    settings.settings_tab = DummySettingsTab(strategy="single_folder")
    thread.settings = settings
    df2 = thread.get_desc_folder_for_post(download_folder, "p1", "Title")
    assert os.path.normpath(df2) == os.path.normpath(os.path.join(download_folder))

    settings.settings_tab = DummySettingsTab(strategy="per_post")
    thread.settings = settings
    df3 = thread.get_desc_folder_for_post(download_folder, "p1", "A Title")
    assert df3.endswith("p1_A_Title")
