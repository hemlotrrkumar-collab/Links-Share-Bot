import json
import os
import asyncio
from config import DB_FILE, ADMINS

DEFAULT_DB = {
    "admins": ADMINS,
    "authorized_users": [],
    "posts": {}, # post_id: {message_id: int, chat_id: int}
    "clones": [], # list of tokens
    "users": [], # list of user_ids who started the bot
    "channels": {} # chat_id: {link: str, owner: int}
}

db_lock = asyncio.Lock()

async def load_db():
    async with db_lock:
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w") as f:
                json.dump(DEFAULT_DB, f, indent=4)
            return DEFAULT_DB
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_DB

async def save_db(db):
    async with db_lock:
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=4)

async def add_user(user_id):
    db = await load_db()
    if user_id not in db["users"]:
        db["users"].append(user_id)
        await save_db(db)

async def is_admin(user_id):
    db = await load_db()
    return user_id in db["admins"]

async def is_authorized(user_id):
    return await is_admin(user_id)

async def add_post(post_id, chat_id, message_id):
    db = await load_db()
    db["posts"][post_id] = {"chat_id": chat_id, "message_id": message_id}
    await save_db(db)

async def get_post(post_id):
    db = await load_db()
    return db["posts"].get(post_id)

async def add_clone(token):
    db = await load_db()
    if token not in db["clones"]:
        db["clones"].append(token)
        await save_db(db)

async def get_clones():
    db = await load_db()
    return db["clones"]

async def add_channel(chat_id, link, owner_id):
    db = await load_db()
    db["channels"][str(chat_id)] = {"link": link, "owner": owner_id}
    await save_db(db)

async def get_channel(chat_id):
    db = await load_db()
    return db["channels"].get(str(chat_id))
