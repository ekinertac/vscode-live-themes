import os
from pprint import pprint
import time
from typing import Any, List, Dict, Optional
import requests
import argparse
from abc import ABC, abstractmethod
import zipfile
import commentjson
import json
import logging
import shutil
from enum import Enum
import tempfile
from tqdm import tqdm
import sentry_sdk
import glob
from collections import defaultdict

sentry_sdk.init(
    dsn="https://a7f5a48af43cecc6ed10281e52b0ebcb@o352105.ingest.us.sentry.io/4507953095245824",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


# Add this at the beginning of the file
def setup_logger(level: str = "INFO") -> None:
    """
    Set up the logger with the specified level.

    Args:
        level (str): The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL, or NONE).
    """
    if level.upper() == "NONE":
        logging.disable(logging.CRITICAL)
    else:
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        logging.basicConfig(
            level=numeric_level, format="%(asctime)s - %(levelname)s - %(message)s"
        )


class ThemeDownloader(ABC):
    """Abstract base class for theme downloaders."""

    @abstractmethod
    def download(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        """
        Download a theme.

        Args:
            theme (Dict[str, Any]): A dictionary containing theme information.

        Returns:
            Dict[str, Any]: An updated theme dictionary with download information.
        """
        pass


class ThemeFetcher(ABC):
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        pass


class ThemeStorage(ABC):
    """Abstract base class for theme storage."""

    @abstractmethod
    def save(self, themes: List[Dict[str, Any]]) -> None:
        """
        Save themes to storage.

        Args:
            themes (List[Dict[str, Any]]): A list of theme dictionaries to save.
        """
        pass

    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        """
        Load themes from storage.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        pass


class ThemeSortOption(Enum):
    MostInstalled = 4
    ByName = 2
    PublishedDate = 10
    Publisher = 3
    ByRating = 12
    TrendingWeekly = 8
    UpdateDate = 1


class VSCodeThemeFetcher(ThemeFetcher):
    """Fetches themes from the Visual Studio Code Marketplace."""

    def __init__(
        self,
        page_size: int = 54,
        max_pages: int = 10,
        sort_option: ThemeSortOption = ThemeSortOption.MostInstalled,
    ) -> None:
        """
        Initialize the VSCodeThemeFetcher.

        Args:
            page_size (int): Number of themes to fetch per page.
            max_pages (int): Maximum number of pages to fetch.
            sort_option (ThemeSortOption): Sorting option for themes.
        """
        self.page_size = page_size
        self.max_pages = max_pages
        self.sort_option = sort_option

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetch themes from the VS Code Marketplace.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        all_themes = []
        with tqdm(total=self.max_pages, desc="Fetching pages", unit="page") as pbar:
            for page_number in range(1, self.max_pages + 1):
                results = self._get_vscode_themes(self.page_size, page_number)
                theme_list = self._build_theme_list(results)
                all_themes.extend(theme_list)
                pbar.update(1)
                pbar.set_postfix({"themes": len(all_themes)})
                time.sleep(1)
        return all_themes

    def _post_data(self, page_number: int) -> Dict[str, Any]:
        """
        Generate the POST data for the VS Code Marketplace API request.

        Args:
            page_number (int): The current page number.

        Returns:
            Dict[str, Any]: The POST data dictionary.
        """
        return {
            "assetTypes": [
                "Microsoft.VisualStudio.Services.Icons.Default",
                "Microsoft.VisualStudio.Services.Icons.Branding",
                "Microsoft.VisualStudio.Services.Icons.Small",
            ],
            "filters": [
                {
                    "criteria": [
                        {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                        {
                            "filterType": 10,
                            "value": 'target:"Microsoft.VisualStudio.Code" ',
                        },
                        {"filterType": 12, "value": "37888"},
                        {"filterType": 5, "value": "Themes"},
                    ],
                    "direction": 2,
                    "pageSize": self.page_size,
                    "pageNumber": page_number,
                    "sortBy": self.sort_option.value,
                    "sortOrder": 0,
                    "pagingToken": None,
                }
            ],
            "flags": 870,
        }

    def _get_vscode_themes(self, page_size: int, page_number: int) -> Dict[str, Any]:
        """
        Fetch themes from the VS Code Marketplace API.

        Args:
            page_size (int): Number of themes to fetch per page.
            page_number (int): The current page number.

        Returns:
            Dict[str, Any]: The API response containing theme data.
        """
        url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
        headers = {
            "accept": "application/json;api-version=7.2-preview.1;excludeUrls=true",
            "accept-language": "en-US,en;q=0.9,tr;q=0.8,es;q=0.7,de;q=0.6,nl;q=0.5,sv;q=0.4,pt;q=0.3,no;q=0.2,cs;q=0.1,ru;q=0.1,mt;q=0.1",
            "cache-control": "no-cache",
            "content-type": "application/json",
        }
        data = self._post_data(page_number)

        with tqdm(
            total=1, desc=f"Fetching page {page_number}", unit="request", leave=False
        ) as pbar:
            response = requests.post(url, headers=headers, json=data)
            pbar.update(1)

        return response.json()

    def _get_download_url(
        self, publisherName: str, extensionName: str, version: str
    ) -> str:
        """
        Generate the download URL for a VS Code extension.

        Args:
            publisherName (str): The name of the extension publisher.
            extensionName (str): The name of the extension.
            version (str): The version of the extension.

        Returns:
            str: The download URL for the extension.
        """
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisherName}/vsextensions/{extensionName}/{version}/vspackage"

    def _build_theme_list(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build a list of themes from the API results.

        Args:
            results (Dict[str, Any]): The API response containing theme data.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        themes = []
        for extension in results["results"][0]["extensions"]:
            if "icons" in [tag.lower() for tag in extension["tags"]]:
                logging.debug(
                    f"Skipping {extension['displayName']} because it has icons"
                )
                continue

            if "Themes" not in extension["categories"]:
                logging.debug(
                    f"Skipping {extension['displayName']} because it is not a theme"
                )
                continue

            statistics = {}
            for stat in extension.get("statistics", []):
                if stat["statisticName"] == "install":
                    statistics["installs"] = stat["value"]
                elif stat["statisticName"] == "weightedRating":
                    statistics["rating"] = stat["value"]

            # MARK: List.json
            themes.append(
                {
                    "categories": extension["categories"],
                    "displayName": extension["displayName"],
                    "publisher": {
                        "displayName": extension["publisher"]["displayName"],
                        "publisherName": extension["publisher"]["publisherName"],
                    },
                    "tags": extension["tags"],
                    "statistics": statistics,
                    "extension": {
                        "extensionId": extension["extensionId"],
                        "extensionName": extension["extensionName"],
                        "latestVersion": extension["versions"][0]["version"],
                        "downloadUrl": self._get_download_url(
                            extension["publisher"]["publisherName"],
                            extension["extensionName"],
                            extension["versions"][0]["version"],
                        ),
                    },
                }
            )
        return themes


class JSONThemeStorage(ThemeStorage):
    """Stores themes in a JSON file."""

    def __init__(self, base_path: str):
        """
        Initialize the JSONThemeStorage.

        Args:
            base_path (str): The base path for storing theme JSON files.
        """
        self.base_path = base_path

    def save(self, themes: List[Dict[str, Any]], sort_option: ThemeSortOption) -> None:
        """
        Save themes to a JSON file.

        Args:
            themes (List[Dict[str, Any]]): A list of theme dictionaries to save.
            sort_option (ThemeSortOption): Sorting option for themes.
        """
        file_name = f"{sort_option.name.lower()}.json"
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, dir=self.base_path, prefix=f"temp_{file_name}"
        )
        try:
            json.dump(themes, temp_file)
            temp_file.close()
            final_path = os.path.join(self.base_path, file_name)
            os.replace(temp_file.name, final_path)
        except Exception as e:
            os.unlink(temp_file.name)
            raise e

    def load(self, sort_option: ThemeSortOption) -> List[Dict[str, Any]]:
        """
        Load themes from a JSON file.

        Args:
            sort_option (ThemeSortOption): Sorting option for themes.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        file_name = f"{sort_option.name.lower()}.json"
        file_path = os.path.join(self.base_path, file_name)
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as file:
            return commentjson.load(file)

    def load_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load themes from all JSON files.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary of theme lists for each sort option.
        """
        all_themes = {}
        for sort_option in ThemeSortOption:
            all_themes[sort_option.name] = self.load(sort_option)
        return all_themes


class VSCodeThemeDownloader(ThemeDownloader):
    """Downloads VS Code themes."""

    def __init__(
        self,
        themes_dir: str = "./themes/themes",
        archives_dir: str = "./themes/archives",
    ):
        """
        Initialize the VSCodeThemeDownloader.

        Args:
            themes_dir (str): The directory to store extracted themes.
            archives_dir (str): The directory to store downloaded theme archives.
        """
        self.themes_dir = themes_dir
        self.archives_dir = archives_dir

        # Create the archives directory if it doesn't exist
        os.makedirs(self.archives_dir, exist_ok=True)
        os.makedirs(self.themes_dir, exist_ok=True)

    def _download_vsix(
        self, publisher_name: str, extension_name: str, version: str, download_url: str
    ) -> str:
        """
        Download the VSIX file for a theme.

        Args:
            publisher_name (str): The name of the theme publisher.
            extension_name (str): The name of the theme extension.
            version (str): The version of the theme.
            download_url (str): The URL to download the VSIX file.

        Returns:
            str: The path to the downloaded VSIX file.
        """
        vsix_path = os.path.join(
            self.archives_dir, f"{publisher_name}.{extension_name}.{version}.vsix"
        )

        if not os.path.exists(vsix_path):
            try:
                response = requests.get(download_url, timeout=30)
                response.raise_for_status()  # Raise an exception for bad status codes
                with open(vsix_path, "wb") as f:
                    f.write(response.content)
                logging.info(
                    f"Downloaded: {publisher_name}.{extension_name} (version {version})"
                )
            except requests.exceptions.RequestException as e:
                logging.error(f"Error downloading VSIX: {str(e)}")
                raise
        else:
            logging.debug(
                f"Skipped download (file exists): {publisher_name}.{extension_name} (version {version})"
            )

        return vsix_path

    def download(self, theme: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        publisher_name = theme["publisher"]["publisherName"]
        extension_name = theme["extension"]["extensionName"]
        version = theme["extension"]["latestVersion"]
        download_url = theme["extension"]["downloadUrl"]

        vsix_path = os.path.join(
            self.archives_dir, f"{publisher_name}.{extension_name}.{version}.vsix"
        )

        if os.path.exists(vsix_path) and not force:
            logging.info(
                f"Theme archive already exists: {publisher_name}.{extension_name} (version {version})"
            )
        else:
            logging.info(f"Downloading theme: {publisher_name}.{extension_name}")
            try:
                vsix_path = self._download_vsix(
                    publisher_name, extension_name, version, download_url
                )
            except Exception as e:
                logging.error(f"Error downloading theme: {str(e)}")
                return theme  # Return original theme if download fails

        theme_dir = self._extract_vsix(
            vsix_path, publisher_name, extension_name, version
        )

        if not theme_dir:
            logging.error(f"Failed to extract theme: {publisher_name}.{extension_name}")
            return theme

        # Delete the VSIX file after successful extraction
        os.remove(vsix_path)
        logging.info(f"Deleted VSIX file: {vsix_path}")

        theme_files = self._get_theme_info(theme_dir)
        if not theme_files:
            logging.warning(
                f"No theme files found for: {publisher_name}.{extension_name}"
            )

        updated_theme = theme.copy()
        updated_theme.update(
            {
                "theme_files": theme_files,
                "theme_dir": theme_dir,
            }
        )

        return updated_theme

    def _extract_vsix(
        self, vsix_path: str, publisher_name: str, extension_name: str, version: str
    ) -> Optional[str]:
        """
        Extract the contents of a VSIX file.

        Args:
            vsix_path (str): The path to the VSIX file.
            publisher_name (str): The name of the theme publisher.
            extension_name (str): The name of the theme extension.
            version (str): The version of the theme.

        Returns:
            Optional[str]: The path to the extracted theme directory, or None if extraction failed.
        """
        theme_dir = os.path.join(
            self.themes_dir, f"{publisher_name}.{extension_name}", version
        )
        try:
            with zipfile.ZipFile(vsix_path, "r") as zip_ref:
                zip_ref.extractall(theme_dir)
            logging.info(f"Extracted: {vsix_path} to {theme_dir}")
            return theme_dir
        except zipfile.BadZipFile:
            logging.error(
                f"Error extracting VSIX file: {vsix_path} is not a valid zip file"
            )
        except Exception as e:
            logging.error(f"Error extracting VSIX file: {str(e)}")

        return None

    def _get_theme_info(self, theme_dir: str) -> List[Dict[str, str]]:
        """
        Get theme information from the package.json file.

        Args:
            theme_dir (str): The directory containing the extracted theme.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing theme file information.
        """
        package_json_path = os.path.join(theme_dir, "extension", "package.json")
        logging.debug(f"Checking package.json: {package_json_path}")

        if not os.path.exists(package_json_path):
            logging.warning(f"package.json not found: {package_json_path}")
            return []

        try:
            with open(package_json_path, "r") as f:
                package_data = json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing package.json: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error reading package.json: {str(e)}")
            return []

        if (
            "contributes" not in package_data
            or "themes" not in package_data["contributes"]
        ):
            logging.warning("No themes found in package.json")
            return []

        theme_files = []
        for theme in package_data["contributes"]["themes"]:
            theme_info = self._process_theme(theme_dir, theme)
            if theme_info:
                theme_files.append(theme_info)

        return theme_files

    def _process_theme(
        self, theme_dir: str, theme: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """
        Process a single theme entry from package.json

        Args:
            theme_dir (str): The directory containing the extracted theme.
            theme (Dict[str, Any]): A theme entry from package.json

        Returns:
            Optional[Dict[str, str]]: A dictionary containing theme file information, or None if invalid.
        """
        relative_theme_path = theme["path"]
        full_theme_path = os.path.join(theme_dir, "extension", relative_theme_path)
        theme_name = theme.get(
            "label", os.path.splitext(os.path.basename(relative_theme_path))[0]
        )

        if not os.path.exists(full_theme_path):
            logging.warning(f"Theme file not found: {full_theme_path}")
            return None

        # Remove "./" from the beginning of the relative_theme_path if present
        cleaned_relative_path = relative_theme_path.lstrip("./")

        # Join theme_dir with the cleaned relative path and remove "./" if present
        full_path = os.path.join(theme_dir, "extension", cleaned_relative_path).lstrip(
            "./"
        )

        logging.debug(f"Added theme: {theme_name}")
        return {
            "file": full_path,
            "name": theme_name,
            "uiTheme": theme.get("uiTheme", ""),
        }


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

                unique_themes[extension_name] = {
                    "label": theme["displayName"],
                    "description": theme["publisher"]["displayName"],
                    "extensionName": extension_name,
                    "detail": f"""{len(theme_files)} {len(theme_files) > 1 and 'Themes' or 'Theme'}""",
                    "themeFiles": theme_files,
                }

        # Convert the dictionary to a list for JSON serialization
        search_index = list(unique_themes.values())

        # Save search index to file
        search_index_path = os.path.join(self.storage.base_path, "search.json")
        with open(search_index_path, "w") as f:
            json.dump(search_index, f, indent=2)

        logging.info(f"Search index saved to {search_index_path}")
        logging.info(f"Total unique themes indexed: {len(search_index)}")
        # MARK: - Search Index


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


def run_command(managers: Dict[ThemeSortOption, ThemeManager], command: str) -> None:
    """
    Run a command using the ThemeManagers.

    Args:
        managers (Dict[ThemeSortOption, ThemeManager]): The ThemeManager instances.
        command (str): The command to run.
    """

    def execute_for_all_managers(method_name: str):
        for manager in managers.values():
            getattr(manager, method_name)()

    def clear_cache():
        for manager in managers.values():
            manager.clear_archives()
            manager.clear_themes()

    def clear_all():
        for manager in managers.values():
            manager.clear_metadata()
        clear_cache()

    def run_all():
        for manager in managers.values():
            manager.fetch_and_save_themes()
            manager.download_themes()

    def delete_archives():
        archives_dir = next(iter(managers.values())).downloader.archives_dir
        if os.path.exists(archives_dir):
            shutil.rmtree(archives_dir)
            os.makedirs(archives_dir)
            logging.info("Deleted all archive files.")
        else:
            logging.warning("Archives directory does not exist.")

    def check_integrity():
        for manager in managers.values():
            manager.check_integrity()

    def cleanup():
        # Get all theme files and package.json files
        all_theme_files = set()
        for manager in managers.values():
            all_theme_files.update(manager.get_all_theme_files())

        # Get all files in the themes directory
        themes_dir = next(iter(managers.values())).downloader.themes_dir
        all_files_in_dir = []
        for path in glob.glob(os.path.join(themes_dir, "**", "*"), recursive=True):
            all_files_in_dir.append(path.replace("./", ""))

        all_files_in_dir = set(all_files_in_dir)

        # Get the difference
        files_to_delete = all_files_in_dir - all_theme_files
        # Delete the difference files
        for file_path in files_to_delete:
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Deleted file: {file_path}")

        # Remove empty directories
        for root, dirs, files in os.walk(themes_dir, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    logging.info(f"Removed empty directory: {dir_path}")

        logging.info("Cleanup completed successfully.")

    def build_search_index():
        # Use the first manager to build the search index
        next(iter(managers.values())).build_search_index()

    command_map = {
        "metadata": lambda: execute_for_all_managers("fetch_and_save_themes"),
        "download": lambda: execute_for_all_managers("download_themes"),
        "clear_metadata": lambda: execute_for_all_managers("clear_metadata"),
        "clear_cache": clear_cache,
        "clear_all": clear_all,
        "all": lambda: (run_all(), delete_archives(), cleanup()),
        "check_integrity": check_integrity,
        "cleanup": cleanup,
        "build_search_index": build_search_index,
    }

    action = command_map.get(command)
    if action:
        action()
    else:
        logging.error(f"Unknown command: {command}")


def main():
    """Main function to run the VS Code Theme Fetcher CLI."""
    parser = argparse.ArgumentParser(description="VSCode Theme Fetcher CLI")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"],
        default="ERROR",
        help="Set the logging level",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=10,
        help="Number of themes to fetch per page. (Default: 10)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum number of pages to fetch. (Default: 1)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "metadata", help="Fetch metadata about themes from the VSCode Marketplace"
    )
    subparsers.add_parser(
        "download", help="Download and extract themes based on the fetched metadata"
    )
    subparsers.add_parser("all", help="Fetch metadata and download all themes")
    subparsers.add_parser("clear_metadata", help="Clear the metadata file")
    subparsers.add_parser("clear_cache", help="Clear the cache")
    subparsers.add_parser("clear_all", help="Clear the metadata, cache, and themes")
    subparsers.add_parser(
        "check_integrity", help="Check the integrity of downloaded theme files"
    )
    subparsers.add_parser(
        "cleanup",
        help="Remove invalid files and empty directories from the themes folder",
    )
    subparsers.add_parser(
        "build_search_index",
        help="Build a search index for all themes and save it as search.json",
    )

    args = parser.parse_args()

    setup_logger(args.log_level)

    managers = {
        sort_option: create_manager(
            page_size=args.page_size, max_pages=args.max_pages, sort_option=sort_option
        )
        for sort_option in ThemeSortOption
    }

    run_command(managers, args.command)


if __name__ == "__main__":
    main()
