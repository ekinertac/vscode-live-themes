import json
import logging
import zipfile
import requests
import os
from typing import Any, Dict, List, Optional

from lib.abstract import ThemeDownloader
from lib.utils import get_quickpick_detail


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

        theme_base_dir = os.path.join(
            self.themes_dir, f"{publisher_name}.{extension_name}"
        )

        # Check if we already have the latest version
        if not force and self._has_latest_version(theme_base_dir, version):
            logging.info(
                f"Skipping download: Already have the latest version of {publisher_name}.{extension_name} (version {version})"
            )
            return self._update_theme_info(theme, theme_base_dir, version)

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

        return self._update_theme_info(theme, theme_dir, version)

    def _has_latest_version(self, theme_base_dir: str, latest_version: str) -> bool:
        """
        Check if we already have the latest version of the theme.

        Args:
            theme_base_dir (str): The base directory for the theme.
            latest_version (str): The latest version of the theme.

        Returns:
            bool: True if we have the latest version, False otherwise.
        """
        if not os.path.exists(theme_base_dir):
            return False

        versions = [
            d
            for d in os.listdir(theme_base_dir)
            if os.path.isdir(os.path.join(theme_base_dir, d))
        ]
        return latest_version in versions

    def _update_theme_info(
        self, theme: Dict[str, Any], theme_dir: str, version: str
    ) -> Dict[str, Any]:
        """
        Update the theme information with the extracted theme files.

        Args:
            theme (Dict[str, Any]): The original theme dictionary.
            theme_dir (str): The directory containing the extracted theme.
            version (str): The version of the theme.

        Returns:
            Dict[str, Any]: The updated theme dictionary.
        """
        theme_files = self._get_theme_info(theme_dir)
        if not theme_files:
            logging.warning(
                f"No theme files found for: {theme['publisher']['publisherName']}.{theme['extension']['extensionName']}"
            )

        updated_theme = theme.copy()

        detail = get_quickpick_detail(len(theme_files), updated_theme["statistics"])

        quickPickData = {
            "label": updated_theme["displayName"],
            "description": updated_theme["publisher"]["displayName"],
            "detail": detail,
        }

        updated_theme.update(
            {
                "theme_files": theme_files,
                "theme_dir": theme_dir,
                "quick_pick": quickPickData,
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
