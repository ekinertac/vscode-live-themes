import json
import logging
import os
import shutil
from tqdm import tqdm
from typing import Any, Dict, List

from lib.downloader import VSCodeThemeDownloader
from lib.storage import JSONThemeStorage
from lib.theme_fetcher import VSCodeThemeFetcher
from lib.utils import get_quickpick_detail
from lib.abstract import ThemeDownloader, ThemeFetcher, ThemeSortOption, ThemeStorage


class ThemeManager:
    """Manages the process of fetching, storing, and downloading themes."""

    def __init__(
        self,
        fetcher: ThemeFetcher,
        storage: ThemeStorage,
        downloader: ThemeDownloader,
        sort_option: ThemeSortOption,
    ):
        """
        Initialize the ThemeManager.

        Args:
            fetcher (ThemeFetcher): An instance of a ThemeFetcher.
            storage (ThemeStorage): An instance of a ThemeStorage.
            downloader (ThemeDownloader): An instance of a ThemeDownloader.
            sort_option (ThemeSortOption): Sorting option for themes.
        """
        self.fetcher = fetcher
        self.storage = storage
        self.downloader = downloader
        self.sort_option = sort_option

    def fetch_and_save_themes(self) -> None:
        """Fetch themes and save them to storage."""
        themes = self.fetcher.fetch()
        self.storage.save(themes, self.sort_option)

    def get_themes(self) -> List[Dict[str, Any]]:
        """
        Get themes from storage.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        return self.storage.load(self.sort_option)

    def download_themes(self) -> None:
        """Download and process all themes in storage."""
        themes = self.get_themes()
        updated_themes = []
        for theme in tqdm(
            themes, desc=f"Downloading themes ({self.sort_option.name})", unit="theme"
        ):
            try:
                updated_theme = self.downloader.download(theme)
                updated_themes.append(updated_theme)
            except Exception as e:
                logging.error(
                    f"Error processing theme {theme.get('displayName', 'Unknown')}: {str(e)}"
                )

        if updated_themes:
            self.storage.save(updated_themes, self.sort_option)
            logging.info(
                f"{len(updated_themes)} themes processed and metadata updated."
            )
        else:
            logging.warning("No themes were successfully processed.")

    # MARK: - Single Download
    def download_single_theme(self, publisher_name: str, extension_name: str) -> None:
        """
        Download and process a single theme.

        Args:
            publisher_name (str): The name of the theme publisher.
            extension_name (str): The name of the theme extension.
        """
        try:
            theme = self.fetcher.fetch_single_theme(publisher_name, extension_name)
            updated_theme = self.downloader.download(theme)

            # Save the single theme to a separate file
            self._save_single_theme(updated_theme)

            logging.info(
                f"Theme {publisher_name}.{extension_name} processed and saved."
            )
        except ValueError as e:
            logging.error(f"Error fetching theme: {str(e)}")
        except Exception as e:
            logging.error(
                f"Error processing theme {publisher_name}.{extension_name}: {str(e)}"
            )
            logging.debug("Exception details:", exc_info=True)

    # MARK: Single Save
    def _save_single_theme(self, theme: Dict[str, Any]) -> None:
        """
        Save a single theme to a separate file.

        Args:
            theme (Dict[str, Any]): The theme data to save.
        """
        single_themes_file = os.path.join(self.storage.base_path, "single_themes.json")

        if os.path.exists(single_themes_file):
            with open(single_themes_file, "r") as f:
                single_themes = json.load(f)
        else:
            single_themes = []

        # Update or add the theme
        theme_index = next(
            (
                i
                for i, t in enumerate(single_themes)
                if t["extension"]["extensionName"]
                == theme["extension"]["extensionName"]
            ),
            None,
        )
        if theme_index is not None:
            single_themes[theme_index] = theme
        else:
            single_themes.append(theme)

        with open(single_themes_file, "w") as f:
            json.dump(single_themes, f)

    def get_single_themes(self) -> List[Dict[str, Any]]:
        """
        Get all single themes that have been downloaded.

        Returns:
            List[Dict[str, Any]]: A list of single theme dictionaries.
        """
        single_themes_file = os.path.join(self.storage.base_path, "single_themes.json")
        if os.path.exists(single_themes_file):
            with open(single_themes_file, "r") as f:
                return json.load(f)
        return []

    # MARK: - Integrity Check
    def check_integrity(self) -> None:
        """Check the integrity of all theme files in theme folders."""
        themes = self.get_themes()
        missing_files = []
        corrupted_files = []

        for theme in tqdm(
            themes,
            desc=f"Checking theme integrity ({self.sort_option.name})",
            unit="theme",
        ):
            theme_dir = theme.get("theme_dir")
            if not theme_dir or not os.path.exists(theme_dir):
                missing_files.append(f"Theme directory not found: {theme_dir}")
                continue

            theme_files = theme.get("theme_files", [])
            for theme_file in theme_files:
                file_path = os.path.join(theme_dir, theme_file["file"])
                if not os.path.exists(file_path):
                    missing_files.append(f"Missing file: {file_path}")
                else:
                    try:
                        with open(file_path, "r") as f:
                            json.load(f)
                    except json.JSONDecodeError:
                        corrupted_files.append(f"Corrupted JSON file: {file_path}")

        if missing_files or corrupted_files:
            logging.error("Integrity check failed:")
            for file in missing_files:
                logging.error(file)
            for file in corrupted_files:
                logging.error(file)
        else:
            logging.info("All theme files passed integrity check.")

    def clear_metadata(self) -> None:
        """Clear the theme metadata file."""
        path = os.path.join(
            self.storage.base_path, f"{self.sort_option.name.lower()}.json"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as file:
            json.dump([], file)

    def clear_archives(self) -> None:
        """Clear the theme cache."""
        path = self.downloader.archives_dir
        if os.path.exists(path):
            for file in os.listdir(path):
                if file != ".gitkeep":
                    os.remove(os.path.join(path, file))
            logging.info("Archives directory cleared successfully.")
        else:
            logging.warning("Archives directory does not exist.")

    def clear_themes(self) -> None:
        """Clear the folders in the theme directory."""
        path = self.downloader.themes_dir
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if item != ".gitkeep":
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        logging.info("Themes directory cleared successfully.")

    def get_all_theme_files(self) -> List[str]:
        """Get all theme file paths and package.json files from theme lists."""
        all_files = set()
        themes = self.get_themes()
        for theme in themes:
            theme_dir = theme.get("theme_dir")
            if theme_dir and os.path.exists(theme_dir):
                # Add theme files
                for theme_file in theme.get("theme_files", []):
                    all_files.add(theme_file["file"].replace("./", ""))

                # Add package.json
                package_json_path = os.path.join(theme_dir, "extension", "package.json")
                all_files.add(package_json_path.replace("./", ""))

        return list(all_files)

    # MARK: - Search Index
    def build_search_index(self) -> None:
        """Build a search index for all themes and save it as search.json."""
        all_themes = []

        # Collect themes from all available sort options
        for sort_option in ThemeSortOption:
            themes = self.storage.load(sort_option)
            all_themes.extend(themes)

        # Add single themes
        all_themes.extend(self.get_single_themes())

        # Remove duplicates based on extensionName and create the search index
        unique_themes = {}
        for theme in all_themes:
            extension_name = theme["extension"]["extensionName"]
            if extension_name not in unique_themes:
                theme_files = []
                if "theme_files" in theme:
                    theme_files = [
                        {
                            "name": tf["name"],
                            "path": "themes/themes/"
                            + os.path.relpath(tf["file"], self.downloader.themes_dir),
                        }
                        for tf in theme["theme_files"]
                    ]

                detail = get_quickpick_detail(
                    len(theme_files), theme.get("statistics", {})
                )
                unique_themes[extension_name] = {
                    "label": theme["displayName"],
                    "description": theme["publisher"]["displayName"],
                    "detail": detail,
                    "extensionName": extension_name,
                    "themeFiles": theme_files,
                }

        # Convert the dictionary to a list for JSON serialization
        search_index = list(unique_themes.values())

        # Save search index to file
        search_index_path = os.path.join(self.storage.base_path, "search.json")
        with open(search_index_path, "w") as f:
            json.dump(search_index, f)

        logging.info(f"Search index saved to {search_index_path}")
        logging.info(f"Total unique themes indexed: {len(search_index)}")


# MARK: - Factory
def create_manager(
    fetcher_class=VSCodeThemeFetcher,
    storage_class=JSONThemeStorage,
    downloader_class=VSCodeThemeDownloader,
    page_size=50,
    max_pages=10,
    storage_path="themes",
    themes_dir="./themes/themes",
    archives_dir="./themes/archives",
    sort_option=ThemeSortOption.MostInstalled,
) -> ThemeManager:
    """
    Create and configure a ThemeManager instance.

    Args:
        fetcher_class: The class to use for fetching themes.
        storage_class: The class to use for storing themes.
        downloader_class: The class to use for downloading themes.
        page_size (int): Number of themes to fetch per page.
        max_pages (int): Maximum number of pages to fetch.
        storage_path (str): Path to the theme metadata storage file.
        themes_dir (str): Directory to store extracted themes.
        archives_dir (str): Directory to store downloaded theme archives.
        sort_option (ThemeSortOption): Sorting option for themes.

    Returns:
        ThemeManager: A configured ThemeManager instance.
    """
    fetcher = fetcher_class(
        page_size=page_size, max_pages=max_pages, sort_option=sort_option
    )
    storage = storage_class(storage_path)
    downloader = downloader_class(themes_dir=themes_dir, archives_dir=archives_dir)
    return ThemeManager(fetcher, storage, downloader, sort_option)
