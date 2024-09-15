import pytest
from server import fetch_themes


def test_fetch_themes():
    themes = fetch_themes()

    # Check if themes is a list
    assert isinstance(themes, list), "fetch_themes() should return a list"

    # Check if the list is not empty
    assert len(themes) > 0, "The list of themes should not be empty"

    # Check if each theme has the expected structure
    for theme in themes:
        assert isinstance(theme, dict), "Each theme should be a dictionary"
        assert "name" in theme, "Each theme should have a 'name' key"
        assert "publisher" in theme, "Each theme should have a 'publisher' key"
        assert "version" in theme, "Each theme should have a 'version' key"


def test_fetch_themes_performance():
    import time

    start_time = time.time()
    fetch_themes()
    end_time = time.time()

    execution_time = end_time - start_time
    assert (
        execution_time < 5
    ), f"fetch_themes() took {execution_time:.2f} seconds, which is too long"
