from ast import For, keyword
from base64 import encode
import os
import logging
import pathlib
import json
import hashlib
import sqlite3
from fastapi import FastAPI, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "image"
origins = [os.environ.get('FRONT_URL', 'http://localhost:3000')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# create database
conn = sqlite3.connect('../db/mercari.sqlite3')
c = conn.cursor()
with open('../db/items.db') as f:
    schema = f.read()
    c.execute(f"""CREATE TABLE IF NOT EXISTS {schema}""")
with open('../db/category.db') as f:
    schema = f.read()
    c.execute(f"""CREATE TABLE IF NOT EXISTS {schema}""")

logger.info("Successfully create database")

conn.commit()
conn.close()


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.get("/items")
def get_item():
    conn = sqlite3.connect('../db/mercari.sqlite3')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    data = c.execute(f"""
            SELECT items.name, category.name AS category
            FROM items
            INNER JOIN category ON items.category_id = category.id""").fetchall()
    if data == []:
        conn.close()
        return "No result"
    else:
        conn.close()
        return {"items": data}


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    conn = sqlite3.connect('../db/mercari.sqlite3')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    data = c.execute(f"""
            SELECT items.name, category.name AS category
            FROM items
            INNER JOIN category ON items.category_id=category.id
            WHERE items.id='{item_id}'""").fetchall()
    print(data)
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
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    data = c.execute(f"""
            SELECT items.name, category.name AS category
            FROM items
            INNER JOIN category ON items.category_id=category.id
            WHERE items.name='{name}'""").fetchall()
    print(data)
    if data == []:
        conn.close()
        return "No result"
    else:
        conn.close()
        return {"items": data}


@ app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = Form(...)):
    logger.info(f"Receive item: {name, category}")
    conn = sqlite3.connect('../db/mercari.sqlite3')
    c = conn.cursor()

    file_name = image.filename
    print(file_name)

    hash = hashlib.sha256(file_name.replace(
        ".jpg", "").encode('utf-8')).hexdigest()

    cate_data = c.execute(
        f"SELECT id, name FROM category WHERE name = '{category}'").fetchall()

    if(cate_data == []):
        c.execute("INSERT INTO category VALUES(?, ?);",
                  (None, category))  # add new category
        cate_id = c.execute(
            f"SELECT id, name FROM category WHERE name = '{category}'").fetchall()[0][0]

        c.execute("INSERT INTO items VALUES(?, ?, ?, ?);",
                  (None, name, cate_id, hash+'.jpg'))
        conn.commit()
        conn.close()
        return {"message": f"List new item {name}"}

    else:
        cate_id = c.execute(
            f"SELECT id, name FROM category WHERE name = '{category}'").fetchall()[0][0]

        c.execute("INSERT INTO items VALUES(?, ?, ?, ?);",
                  (None, name, cate_id, hash+'.jpg'))
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
        logger.info(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)
