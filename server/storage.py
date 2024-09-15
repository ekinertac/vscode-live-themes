from abstract import ThemeSortOption, ThemeStorage
from typing import Any, Dict, List
import tempfile
import json
import os
import commentjson


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
            os.chmod(
                final_path, 0o644
            )  # Set read and write permissions for owner, read for others
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
