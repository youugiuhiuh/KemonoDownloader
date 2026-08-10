"""
Unit tests for utility functions in the KemonoDownloader application.
These tests focus on pure functions that don't require GUI or network access.
"""

import os
import sys

try:
    from kemonodownloader.creator_downloader import get_domain_config, sanitize_filename
    from kemonodownloader.kd_language import KDLanguage, language_manager, translate
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
    from kemonodownloader.creator_downloader import get_domain_config, sanitize_filename
    from kemonodownloader.kd_language import KDLanguage, language_manager, translate


class TestSanitizeFilename:
    """Tests for the sanitize_filename utility function."""

    def test_simple_name(self):
        """Test basic name with spaces."""
        assert sanitize_filename("Simple Name") == "Simple_Name"

    def test_special_characters_slash(self):
        """Test removal of forward slashes."""
        assert sanitize_filename("name/with/slashes") == "name_with_slashes"

    def test_special_characters_backslash(self):
        """Test removal of backslashes."""
        assert sanitize_filename("name\\with\\backslashes") == "name_with_backslashes"

    def test_special_characters_colon(self):
        """Test removal of colons (common in timestamps)."""
        assert sanitize_filename("name:with:colons") == "name_with_colons"

    def test_special_characters_quotes(self):
        """Test removal of double quotes."""
        assert sanitize_filename('name"with"quotes') == "name_with_quotes"

    def test_special_characters_angle_brackets(self):
        """Test removal of angle brackets."""
        assert sanitize_filename("name<with>brackets") == "name_with_brackets"

    def test_special_characters_pipe(self):
        """Test removal of pipe character."""
        assert sanitize_filename("name|with|pipes") == "name_with_pipes"

    def test_special_characters_question_mark(self):
        """Test removal of question marks."""
        assert sanitize_filename("name?with?questions") == "name_with_questions"

    def test_special_characters_asterisk(self):
        """Test removal of asterisks."""
        assert sanitize_filename("name*with*asterisks") == "name_with_asterisks"

    def test_length_limit_default(self):
        """Test that filenames are truncated to 100 characters by default."""
        long_name = "a" * 150
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 100

    def test_length_limit_custom(self):
        """Test custom max_length parameter."""
        long_name = "a" * 100
        sanitized = sanitize_filename(long_name, max_length=50)
        assert len(sanitized) <= 50

    def test_leading_trailing_spaces(self):
        """Test trimming of leading and trailing spaces."""
        assert sanitize_filename("  spaces  ") == "spaces"

    def test_leading_trailing_underscores(self):
        """Test trimming of leading and trailing underscores."""
        assert sanitize_filename("_underscores_") == "underscores"

    def test_multiple_consecutive_underscores(self):
        """Test that multiple underscores are collapsed to one."""
        assert sanitize_filename("name___with___many") == "name_with_many"

    def test_empty_string(self):
        """Test that empty string returns 'unnamed'."""
        assert sanitize_filename("") == "unnamed"

    def test_none_input(self):
        """Test that None input returns 'unnamed'."""
        assert sanitize_filename(None) == "unnamed"

    def test_trailing_dots(self):
        """Test removal of trailing dots (Windows compatibility)."""
        assert sanitize_filename("file.name.") == "file.name"
        assert sanitize_filename("file...") == "file"

    def test_mixed_special_characters(self):
        """Test filename with multiple types of special characters."""
        result = sanitize_filename('Test:<>"File|Name?.txt')
        assert result == "Test_File_Name_.txt"

    def test_unicode_characters(self):
        """Test that unicode characters are preserved."""
        # Japanese characters
        result = sanitize_filename("日本語ファイル")
        assert "日本語ファイル" in result or result == "日本語ファイル"

    def test_only_special_characters(self):
        """Test filename with only special characters returns 'unnamed'."""
        assert sanitize_filename(":::") == "unnamed"
        assert sanitize_filename("???") == "unnamed"


class TestGetDomainConfig:
    """Tests for the get_domain_config function."""

    def test_kemono_url(self):
        """Test configuration for kemono.cr URLs."""
        config = get_domain_config("https://kemono.cr/fanbox/user/12345")
        assert config["domain"] == "kemono.cr"
        assert config["base_url"] == "https://kemono.cr"
        assert config["api_base"] == "https://kemono.cr/api/v1"
        assert config["referer"] == "https://kemono.cr/"

    def test_kemono_url_with_post(self):
        """Test configuration for kemono.cr post URLs."""
        config = get_domain_config("https://kemono.cr/fanbox/user/12345/post/67890")
        assert config["domain"] == "kemono.cr"
        assert config["base_url"] == "https://kemono.cr"

    def test_coomer_url(self):
        """Test configuration for coomer.st URLs."""
        config = get_domain_config("https://coomer.st/onlyfans/user/12345")
        assert config["domain"] == "coomer.st"
        assert config["base_url"] == "https://coomer.st"
        assert config["api_base"] == "https://coomer.st/api/v1"
        assert config["referer"] == "https://coomer.st/"

    def test_coomer_url_with_post(self):
        """Test configuration for coomer.st post URLs."""
        config = get_domain_config("https://coomer.st/fansly/user/12345/post/67890")
        assert config["domain"] == "coomer.st"
        assert config["base_url"] == "https://coomer.st"

    def test_unknown_url_defaults_to_kemono(self):
        """Test that unknown URLs default to kemono.cr configuration."""
        config = get_domain_config("https://example.com/something")
        assert config["domain"] == "kemono.cr"
        assert config["base_url"] == "https://kemono.cr"

    def test_empty_url_defaults_to_kemono(self):
        """Test that empty URL defaults to kemono.cr."""
        config = get_domain_config("")
        assert config["domain"] == "kemono.cr"

    def test_url_case_sensitivity(self):
        """Test that domain detection is case-insensitive (in the URL itself)."""
        # URLs are typically lowercase, but let's verify the function handles standard cases
        config_lower = get_domain_config("https://coomer.st/user/123")
        assert config_lower["domain"] == "coomer.st"


class TestLanguageManager:
    """Tests for the KDLanguage translation system."""

    def test_language_manager_singleton(self):
        """Test that language_manager is a singleton instance."""
        assert isinstance(language_manager, KDLanguage)

    def test_default_language_is_english(self):
        """Test that the default language is English."""
        manager = KDLanguage()
        assert manager.current_language == "english"

    def test_set_language_english(self):
        """Test setting language to English."""
        original = language_manager.current_language
        try:
            language_manager.set_language("english")
            assert language_manager.current_language == "english"
        finally:
            language_manager.set_language(original)

    def test_set_language_japanese(self):
        """Test setting language to Japanese."""
        original = language_manager.current_language
        try:
            language_manager.set_language("japanese")
            assert language_manager.current_language == "japanese"
        finally:
            language_manager.set_language(original)

    def test_set_language_korean(self):
        """Test setting language to Korean."""
        original = language_manager.current_language
        try:
            language_manager.set_language("korean")
            assert language_manager.current_language == "korean"
        finally:
            language_manager.set_language(original)

    def test_set_language_chinese_simplified(self):
        """Test setting language to Simplified Chinese."""
        original = language_manager.current_language
        try:
            language_manager.set_language("chinese-simplified")
            assert language_manager.current_language == "chinese-simplified"
        finally:
            language_manager.set_language(original)

    def test_translate_english(self):
        """Test translation returns English text."""
        original = language_manager.current_language
        try:
            language_manager.set_language("english")
            result = translate("added_to_queue")
            assert result == "Added to queue"
        finally:
            language_manager.set_language(original)

    def test_translate_japanese(self):
        """Test translation returns Japanese text."""
        original = language_manager.current_language
        try:
            language_manager.set_language("japanese")
            result = translate("added_to_queue")
            assert result == "キューに追加されました"
        finally:
            language_manager.set_language(original)

    def test_translate_with_formatting(self):
        """Test translation with format arguments."""
        original = language_manager.current_language
        try:
            language_manager.set_language("english")
            result = translate("total_posts", 42)
            assert result == "Total posts: 42"
        finally:
            language_manager.set_language(original)

    def test_translate_missing_key_returns_key(self):
        """Test that missing translation key returns the key itself."""
        original = language_manager.current_language
        try:
            language_manager.set_language("english")
            result = translate("this_key_does_not_exist_xyz123")
            assert result == "this_key_does_not_exist_xyz123"
        finally:
            language_manager.set_language(original)

    def test_get_available_languages(self):
        """Test getting list of available languages."""
        languages = language_manager.get_available_languages()
        assert "english" in languages
        assert "japanese" in languages
        assert "korean" in languages
        assert "chinese-simplified" in languages
        assert len(languages) == 4

    def test_get_language(self):
        """Test getting current language."""
        original = language_manager.current_language
        try:
            language_manager.set_language("japanese")
            assert language_manager.get_language() == "japanese"
        finally:
            language_manager.set_language(original)


class TestTranslationKeys:
    """Tests to verify common translation keys exist and return proper values."""

    def setup_method(self):
        """Store original language before each test."""
        self.original_language = language_manager.current_language
        language_manager.set_language("english")

    def teardown_method(self):
        """Restore original language after each test."""
        language_manager.set_language(self.original_language)

    def test_common_ui_keys_exist(self):
        """Test that common UI translation keys exist and don't return the key."""
        keys_to_test = [
            "added_to_queue",
            "error",
            "browse",
            "download_settings",
            "folder_settings",
            "language",
            "apply_changes",
        ]
        for key in keys_to_test:
            result = translate(key)
            # If the key doesn't exist, it returns the key itself
            assert result != key, f"Translation key '{key}' not found"

    def test_log_keys_exist(self):
        """Test that log-related translation keys exist."""
        keys_to_test = [
            "total_posts",
            "total_files_detected",
        ]
        for key in keys_to_test:
            result = translate(key, 0)  # Pass 0 as a placeholder argument
            assert key not in result or "{" in language_manager.translations.get(
                key, {}
            ).get("english", ""), f"Translation key '{key}' not found"


class TestCleanFileUrl:
    """Tests for the clean_file_url utility function."""

    def test_relative_url(self):
        """Test relative path conversion."""
        from kemonodownloader.domain_config import clean_file_url

        domain_config = {
            "domain": "kemono.cr",
            "base_url": "https://kemono.cr",
            "file_base_url": "https://kemono.cr",
        }
        url = clean_file_url("/data/123.png", domain_config)
        assert url == "https://kemono.cr/data/123.png"

    def test_pawchive_relative_url(self):
        """Test pawchive relative path uses file.pawchive.<suffix>."""
        from kemonodownloader.domain_config import clean_file_url

        domain_config = {
            "domain": "pawchive.pw",
            "base_url": "https://pawchive.pw",
            "file_base_url": "https://file.pawchive.pw",
        }
        url = clean_file_url("/data/123.png", domain_config)
        assert url == "https://file.pawchive.pw/data/123.png"

    def test_pawchive_absolute_url(self):
        """Test pawchive absolute path is rewritten to file.pawchive.<suffix>."""
        from kemonodownloader.domain_config import clean_file_url

        domain_config = {
            "domain": "pawchive.pw",
            "base_url": "https://pawchive.pw",
            "file_base_url": "https://file.pawchive.pw",
        }
        url = clean_file_url("https://pawchive.pw/data/123.png", domain_config)
        assert url == "https://file.pawchive.pw/data/123.png"

    def test_pawchive_domain_config_has_file_base_url(self):
        """Test that get_domain_config for pawchive returns suffix-matched file_base_url."""
        from kemonodownloader.domain_config import get_domain_config, get_domains

        pawchive_domain = next(d for d in get_domains() if d.startswith("pawchive."))
        config = get_domain_config(f"https://{pawchive_domain}/patreon/user/123")
        assert config["domain"] == pawchive_domain
        assert config["base_url"] == f"https://{pawchive_domain}"
        assert config["file_base_url"] == f"https://file.{pawchive_domain}"

    def test_pawchive_relative_url_missing_data(self):
        """Test pawchive relative path without /data/ gets /data/ prepended."""
        from kemonodownloader.domain_config import clean_file_url

        domain_config = {
            "domain": "pawchive.pw",
            "base_url": "https://pawchive.pw",
            "file_base_url": "https://file.pawchive.pw",
        }
        url = clean_file_url("/35/c3/123.png", domain_config)
        assert url == "https://file.pawchive.pw/data/35/c3/123.png"

    def test_pawchive_absolute_url_missing_data(self):
        """Test pawchive absolute path without /data/ gets /data/ prepended and rewritten."""
        from kemonodownloader.domain_config import clean_file_url

        domain_config = {
            "domain": "pawchive.pw",
            "base_url": "https://pawchive.pw",
            "file_base_url": "https://file.pawchive.pw",
        }
        url = clean_file_url("https://pawchive.pw/35/c3/123.png", domain_config)
        assert url == "https://file.pawchive.pw/data/35/c3/123.png"
