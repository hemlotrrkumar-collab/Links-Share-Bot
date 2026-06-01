import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import API_ID, API_HASH
from database import (
    get_clones, add_user, get_post, get_channel, is_authorized, is_admin,
    add_post, load_db, save_db, add_channel, add_clone, add_admin,
    remove_admin, set_delete_timer, get_delete_timer, set_force_channels,
    get_force_channels, add_random_link, get_random_link_chat_id, remove_random_link
)
from utils import to_small_caps, delete_after
from pyrogram.errors import FloodWait
import uuid

clients = []
fs_setup_state = {} # user_id: {step: str, data: dict}

async def is_subscribed(client, user_id):
    force_channels = await get_force_channels()
    not_subscribed = []
    for ch in force_channels:
        try:
            member = await client.get_chat_member(ch["chat_id"], user_id)
            if member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]:
                continue
            else:
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)
    return not_subscribed

async def help_command(client, message: Message):
    user_id = message.from_user.id
    if not await is_authorized(user_id):
        return

    help_text = to_small_caps(
        "--- ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs ---\n\n"
        "/sᴛᴀʀᴛ - sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n"
        "/ʜᴇʟᴘ - sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ ᴍᴇssᴀɢᴇ\n"
        "/ᴘᴏsᴛ - ᴄʀᴇᴀᴛᴇ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ\n"
        "/ᴄʟᴏɴᴇ [ʙᴏᴛ_ᴛᴏᴋᴇɴ] - ᴄʟᴏɴᴇ ᴛʜɪs ʙᴏᴛ\n"
        "/ʙʀᴏᴀᴅᴄᴀsᴛ - ʙʀᴏᴀᴅᴄᴀsᴛ ᴀ ᴍᴇssᴀɢᴇ\n"
        "/ᴄʜᴀɴɴᴇʟ [ᴄʜᴀᴛ_ɪᴅ] [ʟɪɴᴋ] - sᴇᴛ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ\n"
        "/ᴀᴅᴅ_ᴀᴜᴛʜ [ᴜsᴇʀ_ɪᴅ] - ᴀᴜᴛʜᴏʀɪᴢᴇ ᴀ ᴜsᴇʀ\n"
        "/sᴛᴀᴛs - sʜᴏᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
        "/ᴀᴅᴅᴀᴅᴍɪɴ [ᴜsᴇʀ_ɪᴅ] - ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ\n"
        "/ʀᴇᴍᴏᴠᴇᴀᴅᴍɪɴ [ᴜsᴇʀ_ɪᴅ] - ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ\n"
        "/sᴇᴛᴛɪᴍᴇʀ [sᴇᴄᴏɴᴅs] - sᴇᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ\n"
        "/sᴇᴛꜰs - ᴍᴀɴᴀɢᴇ ꜰᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ"
    )
    timer = await get_delete_timer()
    msg = await message.reply(help_text)
    asyncio.create_task(delete_after([message, msg], timer))

async def start_handler(client, message: Message):
    user_id = message.from_user.id
    text = message.text.split()
    timer = await get_delete_timer()

    await add_user(user_id) # Add user to DB for broadcast

    if len(text) > 1:
        data = text[1]

        # Force sub check
        not_subscribed = await is_subscribed(client, user_id)
        if not_subscribed:
            buttons = []
            for ch in not_subscribed:
                buttons.append([InlineKeyboardButton(to_small_caps("ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ"), url=ch["link"])])
            buttons.append([InlineKeyboardButton(to_small_caps("ᴛʀʏ ᴀɢᴀɪɴ"), url=f"https://t.me/{(await client.get_me()).username}?start={data}")])

            msg = await message.reply(
                to_small_caps("ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ."),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            asyncio.create_task(delete_after([message, msg], timer))
            return

        post_data = await get_post(data)
        if post_data:
            try:
                msg = await client.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=post_data["chat_id"],
                    message_id=post_data["message_id"],
                    protect_content=True
                )
                info_msg = await message.reply(to_small_caps(f"ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {timer} sᴇᴄᴏɴᴅs."))
                asyncio.create_task(delete_after([message, msg, info_msg], timer))
            except Exception as e:
                msg = await message.reply(to_small_caps(f"ᴇʀʀᴏʀ: {str(e)}"))
                asyncio.create_task(delete_after([message, msg], timer))
            return
        elif data.startswith("ch_"):
            chat_id = data.replace("ch_", "").replace("n", "-")
            channel_info = await get_channel(chat_id)
            if channel_info:
                msg = await message.reply(f"{to_small_caps('ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ:')} {channel_info['link']}")
                asyncio.create_task(delete_after([message, msg], timer))
                return
        elif data.startswith("rd_"):
            random_id = data.replace("rd_", "")
            chat_id = await get_random_link_chat_id(random_id)
            if chat_id:
                channel_info = await get_channel(chat_id)
                if channel_info:
                    msg = await message.reply(f"{to_small_caps('ʜᴇʀᴇ ɪs ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ:')} {channel_info['link']}")
                    asyncio.create_task(delete_after([message, msg], timer))
                    return

    if not await is_authorized(user_id):
        msg = await message.reply(to_small_caps("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ."))
        asyncio.create_task(delete_after([message, msg], timer))
        return

    welcome_text = to_small_caps("ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʟɪɴᴋ sʜᴀʀᴇ ʙᴏᴛ.\n\nᴜsᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ.")
    buttons = [
        [InlineKeyboardButton(to_small_caps("ᴄʀᴇᴀᴛᴇ ᴘᴏsᴛ"), callback_data="create_post")],
        [InlineKeyboardButton(to_small_caps("ʙʀᴏᴀᴅᴄᴀsᴛ"), callback_data="broadcast_ui")],
        [InlineKeyboardButton(to_small_caps("ᴄʟᴏɴᴇ ʙᴏᴛ"), callback_data="clone_ui")]
    ]
    msg = await message.reply(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))
    asyncio.create_task(delete_after([message, msg], timer))

async def callback_handler(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if not await is_authorized(user_id):
        await callback_query.answer(to_small_caps("ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ"), show_alert=True)
        return

    timer = await get_delete_timer()
    if data == "create_post":
        msg = await callback_query.message.reply(to_small_caps("ᴜsᴇ /ᴘᴏsᴛ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ."))
        asyncio.create_task(delete_after(msg, timer))
    elif data == "broadcast_ui":
        msg = await callback_query.message.reply(to_small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ /ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ sᴇɴᴅ ɪᴛ."))
        asyncio.create_task(delete_after(msg, timer))
    elif data == "clone_ui":
        msg = await callback_query.message.reply(to_small_caps("ᴜsᴇ /ᴄʟᴏɴᴇ [ʙᴏᴛ_ᴛᴏᴋᴇɴ] ᴛᴏ ᴄʟᴏɴᴇ."))
        asyncio.create_task(delete_after(msg, timer))
    elif data == "fs_list":
        channels = await get_force_channels()
        text = to_small_caps("ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟs:\n\n")
        buttons = []
        for i, ch in enumerate(channels):
            text += f"{i+1}. {ch['chat_id']} ({ch['type']})\n"
            buttons.append([InlineKeyboardButton(to_small_caps(f"ᴅᴇʟᴇᴛᴇ {i+1}"), callback_data=f"fs_del_{i}")])

        if len(channels) < 8:
            buttons.append([InlineKeyboardButton(to_small_caps("ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ"), callback_data="fs_add")])

        msg = await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        asyncio.create_task(delete_after(msg, timer))
    elif data == "fs_add":
        fs_setup_state[user_id] = {"step": "chat_id", "data": {}}
        msg = await callback_query.message.edit_text(to_small_caps("sᴇɴᴅ ᴛʜᴇ ᴄʜᴀᴛ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ ᴏꜰ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ:"))
        asyncio.create_task(delete_after(msg, timer))
    elif data.startswith("fs_del_"):
        index = int(data.split("_")[2])
        channels = await get_force_channels()
        if 0 <= index < len(channels):
            channels.pop(index)
            await set_force_channels(channels)
            await callback_query.answer(to_small_caps("ᴄʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ"))
            # Refresh list
            await callback_handler(client, callback_query)
            return
    elif data.startswith("fs_type_"):
        f_type = data.split("_")[2]
        if user_id in fs_setup_state:
            fs_setup_state[user_id]["data"]["type"] = f_type
            fs_setup_state[user_id]["step"] = "link"
            msg = await callback_query.message.edit_text(to_small_caps("sᴇɴᴅ ᴛʜᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ꜰᴏʀ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ:"))
            asyncio.create_task(delete_after(msg, timer))
    await callback_query.answer()

async def post_command(client, message: Message):
    if not await is_authorized(message.from_user.id):
        return
    timer = await get_delete_timer()
    msg = await message.reply(to_small_caps("ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ʟɪɴᴋ ꜰᴏʀ."))
    asyncio.create_task(delete_after([message, msg], timer))

async def handle_messages(client, message: Message):
    user_id = message.from_user.id
    timer = await get_delete_timer()

    if user_id in fs_setup_state:
        state = fs_setup_state[user_id]
        if state["step"] == "chat_id":
            state["data"]["chat_id"] = message.text
            state["step"] = "type"
            buttons = [
                [InlineKeyboardButton(to_small_caps("ᴘᴜʙʟɪᴄ"), callback_data="fs_type_public")],
                [InlineKeyboardButton(to_small_caps("ᴘʀɪᴠᴀᴛᴇ"), callback_data="fs_type_private")],
                [InlineKeyboardButton(to_small_caps("ʀᴇǫᴜᴇsᴛᴇᴅ"), callback_data="fs_type_requested")]
            ]
            msg = await message.reply(to_small_caps("sᴇʟᴇᴄᴛ ʟɪɴᴋ ᴛʏᴘᴇ:"), reply_markup=InlineKeyboardMarkup(buttons))
            asyncio.create_task(delete_after([message, msg], timer))
            return
        elif state["step"] == "link":
            state["data"]["link"] = message.text
            channels = await get_force_channels()
            channels.append(state["data"])
            await set_force_channels(channels)
            del fs_setup_state[user_id]
            msg = await message.reply(to_small_caps("ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ."))
            asyncio.create_task(delete_after([message, msg], timer))
            return

    if not await is_authorized(user_id):
        asyncio.create_task(delete_after(message, timer))
        return
    post_id = str(uuid.uuid4())[:8]
    await add_post(post_id, message.chat.id, message.id)
    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={post_id}"
    msg = await message.reply(f"{to_small_caps('ʜᴇʀᴇ ɪs ʏᴏᴜʀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ:')}\n\n`{link}`", parse_mode=enums.ParseMode.MARKDOWN)
    asyncio.create_task(delete_after([message, msg], timer))

async def clone_command(client, message: Message):
    if not await is_admin(message.from_user.id): # Cloning strictly admin
        return
    timer = await get_delete_timer()
    text = message.text.split()
    if len(text) < 2:
        msg = await message.reply(to_small_caps("ᴜsᴀɢᴇ: /ᴄʟᴏɴᴇ [ʙᴏᴛ_ᴛᴏᴋᴇɴ]"))
        asyncio.create_task(delete_after([message, msg], timer))
        return
    token = text[1]
    await add_clone(token)
    try:
        new_client = await setup_client(token)
        await new_client.start()
        msg = await message.reply(to_small_caps("ʙᴏᴛ ᴄʟᴏɴᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴀɴᴅ sᴛᴀʀᴛᴇᴅ."))
    except Exception as e:
        msg = await message.reply(to_small_caps(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ᴄʟᴏɴᴇ ʙᴏᴛ: {str(e)}"))
    asyncio.create_task(delete_after([message, msg], timer))

async def broadcast_command(client, message: Message):
    if not await is_authorized(message.from_user.id):
        return
    timer = await get_delete_timer()
    if not message.reply_to_message:
        msg = await message.reply(to_small_caps("ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪᴛ."))
        asyncio.create_task(delete_after([message, msg], timer))
        return
    db = await load_db()
    users = db.get("users", [])
    timer = await get_delete_timer()
    count = 0
    status_msg = await message.reply(to_small_caps("ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ..."))
    for user_id in users:
        try:
            msg = await client.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.reply_to_message.id,
                protect_content=True
            )
            asyncio.create_task(delete_after(msg, timer))
            count += 1
            await asyncio.sleep(0.05) # Rate limiting
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass
    await status_msg.edit_text(to_small_caps(f"ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴛᴏ {count} ᴜsᴇʀs. ᴍᴇssᴀɢᴇs ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ɪɴ {timer} sᴇᴄᴏɴᴅs."))
    asyncio.create_task(delete_after([message, status_msg], timer))

async def channel_command(client, message: Message):
    if not await is_authorized(message.from_user.id):
        return
    text = message.text.split()
    if len(text) < 3:
        await message.reply(to_small_caps("ᴜsᴀɢᴇ: /ᴄʜᴀɴɴᴇʟ [ᴄʜᴀᴛ_ɪᴅ] [ʟɪɴᴋ]"))
        return
    chat_id = text[1]
    link = text[2]
    await add_channel(chat_id, link, message.from_user.id)
    bot_username = (await client.get_me()).username
    timer = await get_delete_timer()

    random_id = str(uuid.uuid4())[:12]
    await add_random_link(random_id, chat_id)

    verify_link = f"https://t.me/{bot_username}?start=rd_{random_id}"
    msg = await message.reply(f"{to_small_caps('ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ sᴇᴛ. ʜᴇʀᴇ ɪs ᴛʜᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʟɪɴᴋ:')}\n\n`{verify_link}`")

    async def rotate_link():
        nonlocal random_id
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timer:
            await asyncio.sleep(8)
            if asyncio.get_event_loop().time() - start_time >= timer:
                break
            old_random_id = random_id
            random_id = str(uuid.uuid4())[:12]
            await add_random_link(random_id, chat_id)
            new_verify_link = f"https://t.me/{bot_username}?start=rd_{random_id}"
            try:
                await msg.edit_text(f"{to_small_caps('ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ sᴇᴛ. ʜᴇʀᴇ ɪs ᴛʜᴇ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ʟɪɴᴋ:')}\n\n`{new_verify_link}`")
                await remove_random_link(old_random_id)
            except Exception:
                break
        await remove_random_link(random_id)

    asyncio.create_task(rotate_link())
    asyncio.create_task(delete_after([message, msg], timer))

async def add_auth_command(client, message: Message):
    if not await is_admin(message.from_user.id):
        return
    timer = await get_delete_timer()
    text = message.text.split()
    if len(text) < 2:
        msg = await message.reply(to_small_caps("ᴜsᴀɢᴇ: /ᴀᴅᴅ_ᴀᴜᴛʜ [ᴜsᴇʀ_ɪᴅ]"))
        asyncio.create_task(delete_after([message, msg], timer))
        return
    try:
        user_id = int(text[1])
        db = await load_db()
        if user_id not in db["authorized_users"]:
            db["authorized_users"].append(user_id)
            await save_db(db)
        msg = await message.reply(to_small_caps(f"ᴜsᴇʀ {user_id} ᴀᴜᴛʜᴏʀɪᴢᴇᴅ."))
    except ValueError:
        msg = await message.reply(to_small_caps("ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ."))
    asyncio.create_task(delete_after([message, msg], timer))

async def stats_command(client, message: Message):
    if not await is_admin(message.from_user.id):
        return
    timer = await get_delete_timer()
    db = await load_db()
    total_users = len(db.get("users", []))
    total_clones = len(db.get("clones", []))
    total_posts = len(db.get("posts", {}))
    stats_text = to_small_caps(
        f"--- ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs ---\n\n"
        f"ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total_users}\n"
        f"ᴛᴏᴛᴀʟ ᴄʟᴏɴᴇs: {total_clones}\n"
        f"ᴛᴏᴛᴀʟ ᴘᴏsᴛs: {total_posts}"
    )
    msg = await message.reply(stats_text)
    asyncio.create_task(delete_after([message, msg], timer))

async def add_admin_command(client, message: Message):
    if not await is_admin(message.from_user.id):
        return
    timer = await get_delete_timer()
    text = message.text.split()
    if len(text) < 2:
        msg = await message.reply(to_small_caps("ᴜsᴀɢᴇ: /ᴀᴅᴅᴀᴅᴍɪɴ [ᴜsᴇʀ_ɪᴅ]"))
        asyncio.create_task(delete_after([message, msg], timer))
        return
    try:
        user_id = int(text[1])
        await add_admin(user_id)
        msg = await message.reply(to_small_caps(f"ᴜsᴇʀ {user_id} ᴀᴅᴅᴇᴅ ᴀs ᴀᴅᴍɪɴ."))
    except ValueError:
        msg = await message.reply(to_small_caps("ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ."))
    asyncio.create_task(delete_after([message, msg], timer))

async def remove_admin_command(client, message: Message):
    if not await is_admin(message.from_user.id):
        return
    timer = await get_delete_timer()
    text = message.text.split()
    if len(text) < 2:
        msg = await message.reply(to_small_caps("ᴜsᴀɢᴇ: /ʀᴇᴍᴏᴠᴇᴀᴅᴍɪɴ [ᴜsᴇʀ_ɪᴅ]"))
        asyncio.create_task(delete_after([message, msg], timer))
        return
    try:
        user_id = int(text[1])
        await remove_admin(user_id)
        msg = await message.reply(to_small_caps(f"ᴜsᴇʀ {user_id} ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴀᴅᴍɪɴs."))
    except ValueError:
        msg = await message.reply(to_small_caps("ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ."))
    asyncio.create_task(delete_after([message, msg], timer))

async def set_timer_command(client, message: Message):
    if not await is_admin(message.from_user.id):
        return
    timer = await get_delete_timer()
    text = message.text.split()
    if len(text) < 2:
        msg = await message.reply(to_small_caps("ᴜsᴀɢᴇ: /sᴇᴛᴛɪᴍᴇʀ [sᴇᴄᴏɴᴅs]"))
        asyncio.create_task(delete_after([message, msg], timer))
        return
    try:
        seconds = int(text[1])
        await set_delete_timer(seconds)
        msg = await message.reply(to_small_caps(f"ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ sᴇᴛ ᴛᴏ {seconds} sᴇᴄᴏɴᴅs."))
    except ValueError:
        msg = await message.reply(to_small_caps("ɪɴᴠᴀʟɪᴅ sᴇᴄᴏɴᴅs."))
    asyncio.create_task(delete_after([message, msg], timer))

async def setfs_command(client, message: Message):
    if not await is_admin(message.from_user.id):
        return
    channels = await get_force_channels()
    text = to_small_caps("ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟs:\n\n")
    buttons = []
    for i, ch in enumerate(channels):
        text += f"{i+1}. {ch['chat_id']} ({ch['type']})\n"
        buttons.append([InlineKeyboardButton(to_small_caps(f"ᴅᴇʟᴇᴛᴇ {i+1}"), callback_data=f"fs_del_{i}")])

    if len(channels) < 8:
        buttons.append([InlineKeyboardButton(to_small_caps("ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ"), callback_data="fs_add")])

    timer = await get_delete_timer()
    msg = await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))
    asyncio.create_task(delete_after([message, msg], timer))

from pyrogram.handlers import MessageHandler, CallbackQueryHandler

async def setup_client(token):
    client = Client(f"session_{token[:10]}", api_id=API_ID, api_hash=API_HASH, bot_token=token)
    client.add_handler(MessageHandler(start_handler, filters.command("start") & filters.private))
    client.add_handler(MessageHandler(help_command, filters.command("help") & filters.private))
    client.add_handler(MessageHandler(post_command, filters.command("post") & filters.private))
    client.add_handler(MessageHandler(clone_command, filters.command("clone") & filters.private))
    client.add_handler(MessageHandler(broadcast_command, filters.command("broadcast") & filters.private))
    client.add_handler(MessageHandler(channel_command, filters.command("channel") & filters.private))
    client.add_handler(MessageHandler(add_auth_command, filters.command("add_auth") & filters.private))
    client.add_handler(MessageHandler(stats_command, filters.command("stats") & filters.private))
    client.add_handler(MessageHandler(add_admin_command, filters.command("addadmin") & filters.private))
    client.add_handler(MessageHandler(remove_admin_command, filters.command("removeadmin") & filters.private))
    client.add_handler(MessageHandler(set_timer_command, filters.command("settimer") & filters.private))
    client.add_handler(MessageHandler(setfs_command, filters.command("setfs") & filters.private))
    client.add_handler(CallbackQueryHandler(callback_handler))
    client.add_handler(MessageHandler(handle_messages, filters.private & ~filters.command(["start", "help", "post", "broadcast", "clone", "add_auth", "channel", "stats", "addadmin", "removeadmin", "settimer", "setfs"])))
    clients.append(client)
    return client

async def start_clones():
    tokens = await get_clones()
    for token in tokens:
        try:
            client = await setup_client(token)
            await client.start()
            print(f"Started clone: {token[:10]}")
        except Exception as e:
            print(f"Failed to start clone {token[:10]}: {e}")

async def stop_clones():
    for client in clients:
        try:
            await client.stop()
        except Exception:
            pass
