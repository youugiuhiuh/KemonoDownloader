from urllib.parse import urljoin

from kemonodownloader.creator_downloader import FilePreparationThread


class DummyCheckbox:
    def __init__(self, checked: bool):
        self._checked = checked

    def isChecked(self):
        return self._checked


class DummyLogger:
    def emit(self, *args, **kwargs):
        # Swallow logs during tests
        return None


def make_thread(main=True, attachments=True, content=True, ext_checks=None):
    if ext_checks is None:
        ext_checks = {
            ".jpg": DummyCheckbox(True),
            ".png": DummyCheckbox(True),
            ".gif": DummyCheckbox(True),
        }
    thread = FilePreparationThread(
        [], {}, ext_checks, main, attachments, content, settings=None
    )
    thread.log = DummyLogger()
    return thread


def test_detect_files_main_attachment_content_and_duplicates():
    thread = make_thread()
    domain_config = {"base_url": "https://kemono.cr"}
    post = {
        "file": {"path": "/files/1.jpg", "name": "origname.jpg"},
        "attachments": [
            {"path": "/files/1.jpg", "name": "origname.jpg"},
            {"path": "/files/2.png", "name": "attach.png"},
        ],
        "content": '<p><img src="/img/1.gif" /></p>',
    }
    allowed = [".jpg", ".png", ".gif"]

    result = thread.detect_files(post, allowed, domain_config)

    expected_main = (
        urljoin(domain_config["base_url"], "/files/1.jpg") + "?f=origname.jpg"
    )
    expected_attach = (
        urljoin(domain_config["base_url"], "/files/2.png") + "?f=attach.png"
    )
    expected_content = urljoin(domain_config["base_url"], "/img/1.gif")

    assert result == [
        ("origname.jpg", expected_main),
        ("attach.png", expected_attach),
        ("1.gif", expected_content),
    ]


def test_detect_files_name_over_path_extension_and_jpeg_matching():
    # If name has .jpeg and allowed contains .jpg, the .jpeg name should match
    thread = make_thread()
    domain_config = {"base_url": "https://kemono.cr"}
    post = {"file": {"path": "/files/noext", "name": "photo.jpeg"}}
    allowed = [".jpg"]

    result = thread.detect_files(post, allowed, domain_config)
    expected = urljoin(domain_config["base_url"], "/files/noext") + "?f=photo.jpeg"
    assert result == [("photo.jpeg", expected)]


def test_detect_files_uses_path_extension_when_name_missing():
    # When name is empty, the path extension should be used and the returned tuple
    # will contain the (possibly empty) name paired with the URL.
    ext_checks = {".png": DummyCheckbox(True)}
    thread = FilePreparationThread(
        [], {}, ext_checks, True, False, False, settings=None
    )
    thread.log = DummyLogger()
    domain_config = {"base_url": "https://kemono.cr"}
    post = {"file": {"path": "/images/pic.PNG", "name": ""}}
    allowed = [".png"]

    result = thread.detect_files(post, allowed, domain_config)
    expected_url = urljoin(domain_config["base_url"], "/images/pic.PNG")
    assert result == [("", expected_url)]
