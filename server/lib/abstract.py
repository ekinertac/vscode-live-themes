from abc import ABC, abstractmethod
from typing import Any, List, Dict
from enum import Enum


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
