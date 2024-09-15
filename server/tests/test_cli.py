import pytest
import os
import json
import tempfile
import subprocess
import shutil


@pytest.fixture(scope="module")
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


py_file = "python main.py"
mainParams = "--page-size=2 --max-pages=1"


@pytest.fixture(scope="module")
def fetch_themes_dir(temp_dir):
    shutil.copy("main.py", temp_dir)
    return temp_dir


@pytest.fixture(scope="module")
def populated_fetch_themes_dir(fetch_themes_dir):
    run_cli(f"{py_file} {mainParams} all", cwd=fetch_themes_dir)
    return fetch_themes_dir


def run_cli(command, cwd=None):
    process = subprocess.Popen(
        command.split(" "),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        universal_newlines=True,
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


# Basic setup tests
def test_fetch_themes_file_exists(fetch_themes_dir):
    assert os.path.exists(
        os.path.join(fetch_themes_dir, "main.py")
    ), "main.py should exist in the temporary directory"


def test_help_command(fetch_themes_dir):
    returncode, stdout, stderr = run_cli(f"{py_file} --help", cwd=fetch_themes_dir)
    assert (
        returncode == 0
    ), f"Expected return code 0, but got {returncode}. Error output: {stderr}"
    assert "VSCode Theme Fetcher CLI" in stdout


# Command execution tests
def test_all_command(populated_fetch_themes_dir):
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "mostinstalled.json")
    )
    assert os.path.exists(os.path.join(populated_fetch_themes_dir, "themes", "themes"))
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "archives")
    )
    most_installed_file = os.path.join(
        populated_fetch_themes_dir, "themes", "mostinstalled.json"
    )
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "byname.json")
    )
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "publisheddate.json")
    )
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "publisher.json")
    )
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "byrating.json")
    )
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "trendingweekly.json")
    )
    assert os.path.exists(
        os.path.join(populated_fetch_themes_dir, "themes", "updatedate.json")
    )

    with open(most_installed_file, "r") as f:
        most_installed = json.load(f)

    theme1 = most_installed[0]
    assert theme1["categories"][0] == "Themes"
    assert len(theme1["theme_files"]) > 0

    theme_file = theme1["theme_files"][0]
    assert os.path.exists(theme_file["file"])

    theme_path = os.path.join(populated_fetch_themes_dir, theme_file["file"])
    assert os.path.exists(theme_path)
