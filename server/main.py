import argparse

import sentry_sdk

from lib.abstract import ThemeSortOption
from lib.command import run_command
from lib.manager import create_manager
from lib.utils import setup_logger

sentry_sdk.init(
    dsn="https://a7f5a48af43cecc6ed10281e52b0ebcb@o352105.ingest.us.sentry.io/4507953095245824",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


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
    subparsers.add_parser(
        "check_integrity", help="Check the integrity of downloaded theme files"
    )
    subparsers.add_parser(
        "cleanup",
        help="Remove invalid files and empty directories from the themes folder",
    )
    single = subparsers.add_parser(
        "single",
        help="Download and process a single theme from the VSCode Marketplace",
    )

    single.add_argument(
        "--theme",
        type=str,
        help="The theme to download and process (e.g. 'publisher.extensionName')",
        required=True,
    )

    subparsers.add_parser(
        "build_search_index",
        help="Build a search index for all themes and save it as search.json",
    )
    subparsers.add_parser("all", help="Fetch metadata and download all themes")

    args = parser.parse_args()

    setup_logger(args.log_level)

    managers = {
        sort_option: create_manager(
            page_size=args.page_size, max_pages=args.max_pages, sort_option=sort_option
        )
        for sort_option in ThemeSortOption
    }

    run_command(managers, args.command, args)


if __name__ == "__main__":
    main()
