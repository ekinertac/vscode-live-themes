import pytest
from unittest.mock import Mock, patch, mock_open
import os
import sys
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_themes import (
    VSCodeThemeFetcher,
    JSONThemeStorage,
    VSCodeThemeDownloader,
    ThemeManager,
    setup_logger,
)


# Test VSCodeThemeFetcher
class TestVSCodeThemeFetcher:
    @pytest.fixture
    def fetcher(self):
        return VSCodeThemeFetcher(page_size=10, max_pages=1)

    def test_post_data(self, fetcher):
        data = fetcher._post_data(1)
        assert data["filters"][0]["pageSize"] == 10
        assert data["filters"][0]["pageNumber"] == 1

    def test_get_download_url(self, fetcher):
        url = fetcher._get_download_url("publisher", "extension", "1.0.0")
        expected = "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/publisher/vsextensions/extension/1.0.0/vspackage"
        assert url == expected

    @patch("fetch_themes.requests.post")
    def test_get_vscode_themes(self, mock_post, fetcher):
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"extensions": []}]}
        mock_post.return_value = mock_response

        result = fetcher._get_vscode_themes(10, 1)
        assert result == {"results": [{"extensions": []}]}

    def test_build_theme_list(self, fetcher):
        mock_results = {
            "results": [
                {
                    "extensions": [
                        {
                            "displayName": "Test Theme",
                            "publisher": {
                                "displayName": "Test Publisher",
                                "publisherName": "testpub",
                            },
                            "extensionName": "test-theme",
                            "versions": [{"version": "1.0.0"}],
                            "categories": ["Themes"],
                            "tags": [],
                            "extensionId": "test-id",
                        }
                    ]
                }
            ]
        }
        themes = fetcher._build_theme_list(mock_results)
        assert len(themes) == 1
        assert themes[0]["displayName"] == "Test Theme"
        assert themes[0]["extension.extensionName"] == "test-theme"

    @patch("fetch_themes.VSCodeThemeFetcher._get_vscode_themes")
    @patch("fetch_themes.time.sleep")
    def test_fetch(self, mock_sleep, mock_get_themes, fetcher):
        mock_get_themes.return_value = {
            "results": [
                {
                    "extensions": [
                        {
                            "displayName": "Test Theme",
                            "publisher": {
                                "displayName": "Test Publisher",
                                "publisherName": "testpub",
                            },
                            "extensionName": "test-theme",
                            "versions": [{"version": "1.0.0"}],
                            "categories": ["Themes"],
                            "tags": [],
                            "extensionId": "test-id",
                        }
                    ]
                }
            ]
        }
        themes = fetcher.fetch()
        assert len(themes) == 1
        assert themes[0]["displayName"] == "Test Theme"


# Test JSONThemeStorage
class TestJSONThemeStorage:
    @pytest.fixture
    def storage(self):
        return JSONThemeStorage("test_themes.json")

    @patch("fetch_themes.os.makedirs")
    @patch("fetch_themes.open", new_callable=mock_open)
    @patch("fetch_themes.json.dump")
    def test_save(self, mock_json_dump, mock_file, mock_makedirs, storage):
        themes = [{"name": "Test Theme"}]
        storage.save(themes)
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once_with("test_themes.json", "w")
        mock_json_dump.assert_called_once_with(themes, mock_file(), indent=2)

    @patch("fetch_themes.os.path.exists")
    @patch(
        "fetch_themes.open",
        new_callable=mock_open,
        read_data='[{"name": "Test Theme"}]',
    )
    def test_load(self, mock_file, mock_exists, storage):
        mock_exists.return_value = True
        themes = storage.load()
        assert len(themes) == 1
        assert themes[0]["name"] == "Test Theme"

    @patch("fetch_themes.os.path.exists")
    def test_load_file_not_exists(self, mock_exists, storage):
        mock_exists.return_value = False
        themes = storage.load()
        assert themes == []


# Test VSCodeThemeDownloader
class TestVSCodeThemeDownloader:
    @pytest.fixture
    def downloader(self):
        return VSCodeThemeDownloader()

    def test_create_theme_dir(self, downloader):
        with patch("fetch_themes.os.makedirs") as mock_makedirs:
            path = downloader._create_theme_dir("publisher", "extension")
            assert path == "./themes/themes/publisher.extension"
            mock_makedirs.assert_called_once_with(path, exist_ok=True)

    @patch("fetch_themes.os.path.exists")
    @patch("fetch_themes.requests.get")
    @patch("fetch_themes.open", new_callable=mock_open)
    def test_download_vsix(self, mock_file, mock_get, mock_exists, downloader):
        mock_exists.return_value = False
        mock_response = Mock()
        mock_response.content = b"test content"
        mock_get.return_value = mock_response

        path = downloader._download_vsix("publisher", "extension", "http://test.com")
        assert path == "./themes/archives/publisher.extension.vsix"
        mock_get.assert_called_once_with("http://test.com")
        mock_file.assert_called_once_with(path, "wb")
        mock_file().write.assert_called_once_with(b"test content")

    @patch("fetch_themes.os.path.exists")
    @patch("fetch_themes.zipfile.ZipFile")
    def test_extract_vsix(self, mock_zipfile, mock_exists, downloader):
        mock_exists.return_value = False
        downloader._extract_vsix("test.vsix", "test_dir")
        mock_zipfile.assert_called_once_with("test.vsix", "r")
        mock_zipfile().__enter__().extractall.assert_called_once_with("test_dir")

    @patch("fetch_themes.os.path.exists")
    @patch(
        "fetch_themes.open",
        new_callable=mock_open,
        read_data='{"contributes": {"themes": [{"path": "themes/test.json", "label": "Test Theme"}]}}',
    )
    def test_get_theme_info(self, mock_file, mock_exists, downloader):
        mock_exists.side_effect = [True, True]  # package.json exists, theme file exists
        theme_files = downloader._get_theme_info("test_dir")
        assert len(theme_files) == 1
        assert theme_files[0]["file"] == "themes/test.json"
        assert theme_files[0]["name"] == "Test Theme"

    @patch.object(VSCodeThemeDownloader, "_create_theme_dir")
    @patch.object(VSCodeThemeDownloader, "_download_vsix")
    @patch.object(VSCodeThemeDownloader, "_extract_vsix")
    @patch.object(VSCodeThemeDownloader, "_get_theme_info")
    def test_download(
        self, mock_get_info, mock_extract, mock_download, mock_create_dir, downloader
    ):
        mock_create_dir.return_value = "test_dir"
        mock_download.return_value = "test.vsix"
        mock_get_info.return_value = [{"file": "test.json", "name": "Test Theme"}]

        theme = {
            "publisher.publisherName": "publisher",
            "extension.extensionName": "extension",
            "extension.downloadUrl": "http://test.com",
        }
        result = downloader.download(theme)

        assert result is not None
        assert result["theme_files"] == [{"file": "test.json", "name": "Test Theme"}]
        assert result["vsix_path"] == "test.vsix"
        assert result["theme_dir"] == "test_dir"


# Test ThemeManager
class TestThemeManager:
    @pytest.fixture
    def manager(self):
        fetcher = Mock()
        storage = Mock()
        downloader = Mock()
        return ThemeManager(fetcher, storage, downloader)

    def test_fetch_and_save_themes(self, manager):
        manager.fetcher.fetch.return_value = [{"name": "Test Theme"}]
        manager.fetch_and_save_themes()
        manager.fetcher.fetch.assert_called_once()
        manager.storage.save.assert_called_once_with([{"name": "Test Theme"}])

    def test_get_themes(self, manager):
        manager.storage.load.return_value = [{"name": "Test Theme"}]
        themes = manager.get_themes()
        assert themes == [{"name": "Test Theme"}]
        manager.storage.load.assert_called_once()

    def test_download_themes(self, manager):
        manager.storage.load.return_value = [{"name": "Theme1"}, {"name": "Theme2"}]
        manager.downloader.download.side_effect = [
            {"name": "Theme1", "downloaded": True},
            None,
        ]
        manager.download_themes()
        assert manager.downloader.download.call_count == 2
        manager.storage.save.assert_called_once_with(
            [{"name": "Theme1", "downloaded": True}]
        )

    @patch("fetch_themes.os.makedirs")
    @patch("fetch_themes.open", new_callable=mock_open)
    def test_clear_metadata(self, mock_file, mock_makedirs, manager):
        manager.clear_metadata()
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once_with("themes/list.json", "w")
        mock_file().write.assert_called_once()


# Test setup_logger
def test_setup_logger():
    with patch("fetch_themes.logging.basicConfig") as mock_config:
        setup_logger("DEBUG")
        mock_config.assert_called_once()
        assert mock_config.call_args[1]["level"] == logging.DEBUG

    with patch("fetch_themes.logging.disable") as mock_disable:
        setup_logger("NONE")
        mock_disable.assert_called_once_with(logging.CRITICAL)

    with pytest.raises(ValueError):
        setup_logger("INVALID")


# Test main function and CLI
@patch("fetch_themes.create_manager")
@patch("fetch_themes.run_command")
@patch("fetch_themes.setup_logger")
def test_main(mock_setup_logger, mock_run_command, mock_create_manager):
    mock_manager = Mock()
    mock_create_manager.return_value = mock_manager

    with patch("sys.argv", ["fetch_themes.py", "--log-level", "DEBUG", "metadata"]):
        from fetch_themes import main

        main()

    mock_setup_logger.assert_called_once_with("DEBUG")
    mock_create_manager.assert_called_once()
    mock_run_command.assert_called_once_with(mock_manager, "metadata")
