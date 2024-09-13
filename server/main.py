from typing import Union

from fastapi import FastAPI

from server import fetch_themes

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/themes/update")
def update_themes():
    fetch_themes.main()
    return {"message": "Themes updated"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
