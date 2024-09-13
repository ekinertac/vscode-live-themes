import os
import time
from typing import Any, List, Dict
import requests
import argparse
from abc import ABC, abstractmethod
import zipfile
import commentjson
import json
import logging


# Add this at the beginning of the file
def setup_logger(level: str = "INFO") -> None:
    """Set up the logger with the specified level.

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
        """Download a theme.

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
        """Save themes to storage.

        Args:
            themes (List[Dict[str, Any]]): A list of theme dictionaries to save.
        """
        pass

    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        """Load themes from storage.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        pass


class VSCodeThemeFetcher(ThemeFetcher):
    """Fetches themes from the Visual Studio Code Marketplace."""

    def __init__(self, page_size: int = 54, max_pages: int = 10) -> None:
        """Initialize the VSCodeThemeFetcher.

        Args:
            page_size (int): Number of themes to fetch per page.
            max_pages (int): Maximum number of pages to fetch.
        """
        self.page_size = page_size
        self.max_pages = max_pages

    def fetch(self) -> List[Dict[str, Any]]:
        """Fetch themes from the VS Code Marketplace.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        all_themes = []
        for page_number in range(1, self.max_pages + 1):
            results = self._get_vscode_themes(self.page_size, page_number)
            theme_list = self._build_theme_list(results)
            all_themes.extend(theme_list)
            time.sleep(1)
        return all_themes

    def _post_data(self, page_number: int) -> Dict[str, Any]:
        """Generate the POST data for the VS Code Marketplace API request.

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
                    "sortBy": 4,
                    "sortOrder": 0,
                    "pagingToken": None,
                }
            ],
            "flags": 870,
        }

    def _get_vscode_themes(self, page_size: int, page_number: int) -> Dict[str, Any]:
        """Fetch themes from the VS Code Marketplace API.

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
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def _get_download_url(
        self, publisherName: str, extensionName: str, version: str
    ) -> str:
        """Generate the download URL for a VS Code extension.

        Args:
            publisherName (str): The name of the extension publisher.
            extensionName (str): The name of the extension.
            version (str): The version of the extension.

        Returns:
            str: The download URL for the extension.
        """
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisherName}/vsextensions/{extensionName}/{version}/vspackage"

    def _build_theme_list(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build a list of themes from the API results.

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

            themes.append(
                {
                    "categories": extension["categories"],
                    "displayName": extension["displayName"],
                    "publisher.displayName": extension["publisher"]["displayName"],
                    "publisher.publisherName": extension["publisher"]["publisherName"],
                    "tags": extension["tags"],
                    "extension.extensionId": extension["extensionId"],
                    "extension.extensionName": extension["extensionName"],
                    "extension.latestVersion": extension["versions"][0]["version"],
                    "extension.downloadUrl": self._get_download_url(
                        extension["publisher"]["publisherName"],
                        extension["extensionName"],
                        extension["versions"][0]["version"],
                    ),
                }
            )
        return themes


class JSONThemeStorage(ThemeStorage):
    """Stores themes in a JSON file."""

    def __init__(self, file_path: str):
        """Initialize the JSONThemeStorage.

        Args:
            file_path (str): The path to the JSON file for storing themes.
        """
        self.file_path = file_path

    def save(self, themes: List[Dict[str, Any]]) -> None:
        """Save themes to a JSON file.

        Args:
            themes (List[Dict[str, Any]]): A list of theme dictionaries to save.
        """
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as file:
            json.dump(themes, file, indent=2)

    def load(self) -> List[Dict[str, Any]]:
        """Load themes from a JSON file.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r") as file:
            return commentjson.load(file)


class VSCodeThemeDownloader(ThemeDownloader):
    """Downloads VS Code themes."""

    def __init__(
        self,
        themes_dir: str = "./themes/themes",
        archives_dir: str = "./themes/archives",
    ):
        """Initialize the VSCodeThemeDownloader.

        Args:
            themes_dir (str): The directory to store extracted themes.
            archives_dir (str): The directory to store downloaded theme archives.
        """
        self.themes_dir = themes_dir
        self.archives_dir = archives_dir

    def download(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        """Download and process a VS Code theme.

        Args:
            theme (Dict[str, Any]): A dictionary containing theme information.

        Returns:
            Dict[str, Any]: An updated theme dictionary with download information.
        """
        publisher_name = theme["publisher.publisherName"]
        extension_name = theme["extension.extensionName"]
        download_url = theme["extension.downloadUrl"]

        logging.info(f"Processing theme: {publisher_name}.{extension_name}")

        theme_dir = self._create_theme_dir(publisher_name, extension_name)
        vsix_path = self._download_vsix(publisher_name, extension_name, download_url)
        self._extract_vsix(vsix_path, theme_dir)
        theme_files = self._get_theme_info(theme_dir)

        if not theme_files:
            logging.warning(
                f"No theme files found for: {publisher_name}.{extension_name}"
            )
            return None

        updated_theme = theme.copy()
        updated_theme.update(
            {
                "theme_files": theme_files,
                "vsix_path": vsix_path,
                "theme_dir": theme_dir,
            }
        )

        logging.info(f"Successfully processed theme: {publisher_name}.{extension_name}")
        return updated_theme

    def _create_theme_dir(self, publisher_name: str, extension_name: str) -> str:
        """Create a directory for storing the theme.

        Args:
            publisher_name (str): The name of the theme publisher.
            extension_name (str): The name of the theme extension.

        Returns:
            str: The path to the created theme directory.
        """
        theme_dir = f"{self.themes_dir}/{publisher_name}.{extension_name}"
        os.makedirs(theme_dir, exist_ok=True)
        return theme_dir

    def _download_vsix(
        self, publisher_name: str, extension_name: str, download_url: str
    ) -> str:
        """Download the VSIX file for a theme.

        Args:
            publisher_name (str): The name of the theme publisher.
            extension_name (str): The name of the theme extension.
            download_url (str): The URL to download the VSIX file.

        Returns:
            str: The path to the downloaded VSIX file.
        """
        os.makedirs(self.archives_dir, exist_ok=True)
        vsix_path = f"{self.archives_dir}/{publisher_name}.{extension_name}.vsix"

        if not os.path.exists(vsix_path):
            response = requests.get(download_url)
            with open(vsix_path, "wb") as f:
                f.write(response.content)
            logging.info(f"Downloaded: {publisher_name}.{extension_name}")
        else:
            logging.debug(
                f"Skipped download (file exists): {publisher_name}.{extension_name}"
            )

        return vsix_path

    def _extract_vsix(self, vsix_path: str, theme_dir: str) -> None:
        """Extract the contents of a VSIX file.

        Args:
            vsix_path (str): The path to the VSIX file.
            theme_dir (str): The directory to extract the contents to.
        """
        with zipfile.ZipFile(vsix_path, "r") as zip_ref:
            zip_ref.extractall(theme_dir)
        logging.info(f"Extracted: {vsix_path}")

    def _get_theme_info(self, theme_dir: str) -> List[Dict[str, str]]:
        """Get theme information from the package.json file.

        Args:
            theme_dir (str): The directory containing the extracted theme.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing theme file information.
        """
        package_json_path = os.path.join(theme_dir, "extension", "package.json")
        theme_files = []

        logging.debug(f"Checking package.json: {package_json_path}")

        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)

                if (
                    "contributes" in package_data
                    and "themes" in package_data["contributes"]
                ):
                    for theme in package_data["contributes"]["themes"]:
                        relative_theme_path = theme["path"]
                        full_theme_path = os.path.join(
                            theme_dir, "extension", relative_theme_path
                        )
                        theme_name = theme.get(
                            "label",
                            os.path.splitext(os.path.basename(relative_theme_path))[0],
                        )

                        if os.path.exists(full_theme_path):
                            theme_files.append(
                                {"file": relative_theme_path, "name": theme_name}
                            )
                            logging.debug(f"Added theme: {theme_name}")
                        else:
                            logging.warning(f"Theme file not found: {full_theme_path}")
                else:
                    logging.warning("No themes found in package.json")
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing package.json: {str(e)}")
            except Exception as e:
                logging.error(f"Error reading package.json: {str(e)}")
        else:
            logging.warning(f"package.json not found: {package_json_path}")

        return theme_files


class ThemeManager:
    """Manages the process of fetching, storing, and downloading themes."""

    def __init__(
        self, fetcher: ThemeFetcher, storage: ThemeStorage, downloader: ThemeDownloader
    ):
        """Initialize the ThemeManager.

        Args:
            fetcher (ThemeFetcher): An instance of a ThemeFetcher.
            storage (ThemeStorage): An instance of a ThemeStorage.
            downloader (ThemeDownloader): An instance of a ThemeDownloader.
        """
        self.fetcher = fetcher
        self.storage = storage
        self.downloader = downloader

    def fetch_and_save_themes(self) -> None:
        """Fetch themes and save them to storage."""
        themes = self.fetcher.fetch()
        self.storage.save(themes)

    def get_themes(self) -> List[Dict[str, Any]]:
        """Get themes from storage.

        Returns:
            List[Dict[str, Any]]: A list of theme dictionaries.
        """
        return self.storage.load()

    def download_themes(self) -> None:
        """Download and process all themes in storage."""
        themes = self.get_themes()
        updated_themes = []
        for theme in themes:
            updated_theme = self.downloader.download(theme)
            if updated_theme is not None:
                updated_themes.append(updated_theme)
        self.storage.save(updated_themes)
        logging.info(
            f"All themes downloaded and metadata updated. {len(updated_themes)} valid themes found."
        )

    def clear_metadata(self) -> None:
        """Clear the theme metadata file."""
        path = "themes/list.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as file:
            commentjson.dump([], file)


def create_manager(
    fetcher_class=VSCodeThemeFetcher,
    storage_class=JSONThemeStorage,
    downloader_class=VSCodeThemeDownloader,
    page_size=10,
    max_pages=1,
    storage_path="themes/list.json",
    themes_dir="./themes/themes",
    archives_dir="./themes/archives",
) -> ThemeManager:
    """Create and configure a ThemeManager instance.

    Args:
        fetcher_class: The class to use for fetching themes.
        storage_class: The class to use for storing themes.
        downloader_class: The class to use for downloading themes.
        page_size (int): Number of themes to fetch per page.
        max_pages (int): Maximum number of pages to fetch.
        storage_path (str): Path to the theme metadata storage file.
        themes_dir (str): Directory to store extracted themes.
        archives_dir (str): Directory to store downloaded theme archives.

    Returns:
        ThemeManager: A configured ThemeManager instance.
    """
    fetcher = fetcher_class(page_size=page_size, max_pages=max_pages)
    storage = storage_class(storage_path)
    downloader = downloader_class(themes_dir=themes_dir, archives_dir=archives_dir)
    return ThemeManager(fetcher, storage, downloader)


def run_command(manager: ThemeManager, command: str) -> None:
    """Run a command using the ThemeManager.

    Args:
        manager (ThemeManager): The ThemeManager instance.
        command (str): The command to run ('metadata', 'download', or 'all').
    """
    if command == "metadata":
        manager.fetch_and_save_themes()
        # count = len(manager.get_themes())
        # print(f"{count} themes fetched and saved successfully.")

    elif command == "download":
        manager.download_themes()

    elif command == "all":
        manager.clear_metadata()
        manager.fetch_and_save_themes()
        manager.download_themes()
        # count = len(manager.get_themes())
        # print(f"{count} themes downloaded and extracted successfully.")


def main():
    """Main function to run the VS Code Theme Fetcher CLI."""
    parser = argparse.ArgumentParser(description="VSCode Theme Fetcher CLI")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NONE"],
        default="INFO",
        help="Set the logging level",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "metadata", help="Fetch metadata about themes from the VSCode Marketplace"
    )
    subparsers.add_parser(
        "download", help="Download and extract themes based on the fetched metadata"
    )
    subparsers.add_parser("all", help="Fetch metadata and download all themes")

    args = parser.parse_args()

    setup_logger(args.log_level)

    manager = create_manager()
    run_command(manager, args.command)


if __name__ == "__main__":
    main()
