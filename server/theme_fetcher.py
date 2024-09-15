import logging
from typing import Any, Dict, List

import requests
from tqdm import tqdm
from abstract import ThemeFetcher, ThemeSortOption


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
                # time.sleep(1)
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

                if stat["statisticName"] == "averagerating":
                    statistics["rating"] = stat["value"]

                if stat["statisticName"] == "ratingcount":
                    statistics["ratingcount"] = stat["value"]

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
