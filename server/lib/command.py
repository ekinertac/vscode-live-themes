import glob
import logging
import os
import shutil
from typing import Dict

from lib.abstract import ThemeSortOption
from lib.manager import ThemeManager


def run_command(
    managers: Dict[ThemeSortOption, ThemeManager], command: str, args: object
) -> None:
    """
    Run a command using the ThemeManagers.

    Args:
        managers (Dict[ThemeSortOption, ThemeManager]): The ThemeManager instances.
        command (str): The command to run.
        args (object): The parsed command-line arguments.
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

            # Process single themes
            single_themes = manager.get_single_themes()
            for theme in single_themes:
                publisher_name = theme["publisher"]["publisherName"]
                extension_name = theme["extension"]["extensionName"]
                manager.download_single_theme(publisher_name, extension_name)

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

    def download_single_theme():
        if args.theme:
            try:
                publisher_name, extension_name = args.theme.split(".", 1)
                for manager in managers.values():
                    manager.download_single_theme(publisher_name, extension_name)
            except ValueError:
                logging.error(
                    "Invalid theme format. Please use 'publisher.extensionName'"
                )
        else:
            logging.error("No theme specified. Use --theme publisher.extensionName")

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
        "single": download_single_theme,
        "all": lambda: (
            run_all(),
            delete_archives(),
            build_search_index(),
            cleanup(),
        ),
        "check_integrity": check_integrity,
        "cleanup": cleanup,
        "build_search_index": build_search_index,
    }

    action = command_map.get(command)
    if action:
        action()
    else:
        logging.error(f"Unknown command: {command}")
