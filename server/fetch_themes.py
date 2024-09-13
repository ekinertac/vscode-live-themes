import os
import time
from typing import Any, List, Dict
from tqdm import tqdm
import requests
import argparse
from abc import ABC, abstractmethod
import zipfile
import commentjson


class ThemeFetcher(ABC):
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        pass


class VSCodeThemeFetcher(ThemeFetcher):
    def __init__(self, page_size: int = 54, max_pages: int = 10):
        self.page_size = page_size
        self.max_pages = max_pages

    def fetch(self) -> List[Dict[str, Any]]:
        all_themes = []
        for page_number in tqdm(range(1, self.max_pages + 1)):
            results = self._get_vscode_themes(self.page_size, page_number)
            theme_list = self._build_theme_list(results)
            all_themes.extend(theme_list)
            time.sleep(1)
        return all_themes

    def _post_data(self, page_number: int) -> Dict[str, Any]:
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
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisherName}/vsextensions/{extensionName}/{version}/vspackage"

    def _build_theme_list(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        themes = []
        for extension in results["results"][0]["extensions"]:
            # Skip if "icons" is in the tags
            if "icons" in [tag.lower() for tag in extension["tags"]]:
                continue

            themes.append(
                {
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


class ThemeStorage(ABC):
    @abstractmethod
    def save(self, themes: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        pass


class JSONThemeStorage(ThemeStorage):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def save(self, themes: List[Dict[str, Any]]) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as file:
            commentjson.dump(themes, file)

    def load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r") as file:
            return commentjson.load(file)


class ThemeDownloader(ABC):
    @abstractmethod
    def download(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        pass


class VSCodeThemeDownloader(ThemeDownloader):
    def __init__(
        self,
        themes_dir: str = "./themes/themes",
        archives_dir: str = "./themes/archives",
    ):
        self.themes_dir = themes_dir
        self.archives_dir = archives_dir

    def download(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        publisher_name = theme["publisher.publisherName"]
        extension_name = theme["extension.extensionName"]
        download_url = theme["extension.downloadUrl"]

        theme_dir = self._create_theme_dir(publisher_name, extension_name)
        vsix_path = self._download_vsix(publisher_name, extension_name, download_url)
        self._extract_vsix(vsix_path, theme_dir)
        theme_files = self._get_theme_info(theme_dir)

        if not theme_files:
            # If no themes found, return None to indicate this extension should be removed
            return None

        updated_theme = theme.copy()
        updated_theme.update(
            {
                "theme_files": theme_files,
                "vsix_path": vsix_path,
            }
        )

        return updated_theme

    def _create_theme_dir(self, publisher_name: str, extension_name: str) -> str:
        theme_dir = f"{self.themes_dir}/{publisher_name}.{extension_name}"
        os.makedirs(theme_dir, exist_ok=True)
        return theme_dir

    def _download_vsix(
        self, publisher_name: str, extension_name: str, download_url: str
    ) -> str:
        os.makedirs(self.archives_dir, exist_ok=True)
        vsix_path = f"{self.archives_dir}/{publisher_name}.{extension_name}.vsix"

        if not os.path.exists(vsix_path):
            response = requests.get(download_url)
            with open(vsix_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {publisher_name}.{extension_name}")
        else:
            print(f"Skipped download (file exists): {publisher_name}.{extension_name}")

        return vsix_path

    def _extract_vsix(self, vsix_path: str, theme_dir: str) -> None:
        extension_themes_dir = f"{theme_dir}/extension/themes"
        if not os.path.exists(extension_themes_dir):
            with zipfile.ZipFile(vsix_path, "r") as zip_ref:
                zip_ref.extractall(theme_dir)
            print(f"Extracted: {vsix_path}")
        else:
            print(f"Skipped extraction (already extracted): {vsix_path}")

    def _get_theme_info(self, theme_dir: str) -> List[Dict[str, str]]:
        extension_themes_dir = f"{theme_dir}/extension/themes"
        theme_files = []

        if os.path.exists(extension_themes_dir):
            for file in os.listdir(extension_themes_dir):
                if file.endswith(".json"):
                    theme_path = os.path.join(extension_themes_dir, file)
                    try:
                        with open(theme_path, "r") as f:
                            theme_data = commentjson.load(f)
                            if "name" in theme_data:
                                theme_name = theme_data["name"]
                                theme_files.append({"file": file, "name": theme_name})
                    except ValueError as e:
                        print(
                            f"Warning: Unable to parse JSON file: {theme_path}. Error: {str(e)}"
                        )
                    except Exception as e:
                        print(f"Error reading theme file {theme_path}: {str(e)}")

        return theme_files


class ThemeManager:
    def __init__(
        self, fetcher: ThemeFetcher, storage: ThemeStorage, downloader: ThemeDownloader
    ):
        self.fetcher = fetcher
        self.storage = storage
        self.downloader = downloader

    def fetch_and_save_themes(self) -> None:
        themes = self.fetcher.fetch()
        self.storage.save(themes)

    def get_themes(self) -> List[Dict[str, Any]]:
        return self.storage.load()

    def download_themes(self) -> None:
        themes = self.get_themes()
        updated_themes = []
        for theme in tqdm(themes, desc="Downloading themes"):
            updated_theme = self.downloader.download(theme)
            if updated_theme is not None:
                updated_themes.append(updated_theme)
        self.storage.save(updated_themes)
        print(
            f"All themes downloaded and metadata updated. {len(updated_themes)} valid themes found."
        )


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
    fetcher = fetcher_class(page_size=page_size, max_pages=max_pages)
    storage = storage_class(storage_path)
    downloader = downloader_class(themes_dir=themes_dir, archives_dir=archives_dir)
    return ThemeManager(fetcher, storage, downloader)


def clear_metadata():
    path = "themes/list.json"

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        commentjson.dump([], file)


def run_command(manager: ThemeManager, command: str) -> None:
    if command == "metadata":
        manager.fetch_and_save_themes()
        count = len(manager.get_themes())
        print(f"{count} themes fetched and saved successfully.")
    elif command == "download":
        manager.download_themes()
    elif command == "all":
        clear_metadata()
        manager.fetch_and_save_themes()
        manager.download_themes()
        count = len(manager.get_themes())
        print(f"{count} themes downloaded and extracted successfully.")


def main():
    parser = argparse.ArgumentParser(description="VSCode Theme Fetcher CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "metadata", help="Fetch metadata about themes from the VSCode Marketplace"
    )
    subparsers.add_parser(
        "download", help="Download and extract themes based on the fetched metadata"
    )
    subparsers.add_parser("all", help="Fetch metadata and download all themes")

    args = parser.parse_args()

    manager = create_manager()
    run_command(manager, args.command)


if __name__ == "__main__":
    main()
