import os
from typing import Union

import commentjson
from fastapi import FastAPI


app = FastAPI()
theme_folder = os.path.join(os.path.dirname(__file__), "themes")
theme_list_path = os.path.join(theme_folder, "list.json")
theme_archives_path = os.path.join(theme_folder, "archives")


def read_file_contents(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/themes/update")
def update_themes():
    return {"message": "Themes updated"}


@app.get("/themes/list")
def list_themes():
    contents = read_file_contents(theme_list_path)
    return commentjson.loads(contents)
