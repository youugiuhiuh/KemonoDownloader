from types import SimpleNamespace
from unittest.mock import MagicMock


def test_extension_tab_renders(qapp, monkeypatch):
    # Make translate return the key to simplify assertions
    monkeypatch.setattr("kemonodownloader.kd_language.translate", lambda s, *a, **k: s)

    from kemonodownloader.kd_extension import ExtensionTab

    parent = SimpleNamespace()
    # Provide a settings_tab with required attributes
    parent.settings_tab = SimpleNamespace(
        get_font=lambda: "Arial",
        language_changed=SimpleNamespace(connect=MagicMock()),
        font_changed=SimpleNamespace(connect=MagicMock()),
    )

    tab = ExtensionTab(parent)

    # Ensure UI elements were created
    assert tab.content_layout.count() > 0
    # _get_font_family should use parent's settings_tab
    assert tab._get_font_family() == "Arial"
    # Refresh UI should not raise
    tab.refresh_ui()


def test_help_tab_renders(qapp, monkeypatch):
    monkeypatch.setattr("kemonodownloader.kd_language.translate", lambda s, *a, **k: s)

    from kemonodownloader.kd_help import HelpTab

    parent = SimpleNamespace()
    parent.settings_tab = SimpleNamespace(
        get_font=lambda: "Times New Roman",
        language_changed=SimpleNamespace(connect=MagicMock()),
        font_changed=SimpleNamespace(connect=MagicMock()),
    )

    tab = HelpTab(parent)
    assert tab.content_layout.count() > 0
    assert tab._get_font_family() == "Times New Roman"
    tab.refresh_ui()
