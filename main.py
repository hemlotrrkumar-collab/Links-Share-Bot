import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from clone_manager import start_clones, stop_clones, setup_client

async def main():
    app = await setup_client(BOT_TOKEN)
    await app.start()
    await start_clones()
    print("Bot started...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.run_until_complete(stop_clones())
