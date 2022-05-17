from ast import keyword
import os
import logging
import pathlib
import json
import hashlib
import sqlite3
from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get('FRONT_URL', 'http://localhost:3000')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Hello, world!"}


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.get("/items")
def get_item():
    conn = sqlite3.connect('../db/mercari.sqlite3')
    # logger.info("Successfully connect to db")
    conn.row_factory = dict_factory
    c = conn.cursor()
    data = c.execute("SELECT name, category FROM items").fetchall()
    if data == []:
        conn.close()
        return "No result"
    else:
        dic = {"items": data}
        conn.close()
        return dic


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    conn = sqlite3.connect('../db/mercari.sqlite3')
    # logger.info("Successfully connect to db")
    conn.row_factory = dict_factory
    c = conn.cursor()
    data = c.execute(
        f"SELECT name, category FROM items WHERE id = {item_id}").fetchall()
    if data == []:
        conn.close()
        return "No result"
    else:
        conn.close()
        return data[0]


@app.get("/search")
def search(name: str = Query(..., alias="keyword")):
    conn = sqlite3.connect('../db/mercari.sqlite3')
    # logger.info("Successfully connect to db")
    conn.row_factory = dict_factory
    c = conn.cursor()
    data = c.execute(
        f"SELECT name, category FROM items WHERE name = '{name}'").fetchall()
    if data == []:
        conn.close()
        return "No result"
    else:
        dic = {"items": data}
        conn.close()
        return dic


id = int(1)


@ app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: str = Form(...)):
    global id
    logger.info(f"Receive item: {name, category}")
    # logger.info("Successfully connect to db")
    conn = sqlite3.connect('../db/mercari.sqlite3')
    c = conn.cursor()

    with open(image, "rb") as f:
        bytes = f.read()
        hash = hashlib.sha256(bytes).hexdigest()
    c.execute(
        f"INSERT INTO items VALUES ('{id}', '{name}','{category}', '{hash}.jpg')")
    id += 1
    print(id)
    conn.commit()
    conn.close()
    return {"message": f"List new item {name}"}


@ app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename
    if not image_filename.endswith(".jpg"):
        raise HTTPException(
            status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)
