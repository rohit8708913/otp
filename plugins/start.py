import asyncio
import base64
import logging
import os
import random
import re
import string 
import string as piroayush
import time
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *
from config import *
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from datetime import datetime, timedelta


SECONDS = TIME 

# Enable logging
logging.basicConfig(level=logging.INFO)

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    logging.info(f"Received /start command from user ID: {id}")

    if not await present_user(id):
        try:
            await add_user(id)
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            return

    text = message.text
    verify_status = await get_verify_status(id)
    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await update_verify_status(id, is_verified=False)

    is_premium = await is_premium_user(id)
    
    logging.info(f"Verify status: {verify_status}")
    logging.info(f"Is premium: {is_premium}")

    try:
        base64_string = text.split(" ", 1)[1]
    except IndexError:
        base64_string = None

    if base64_string:
        string = await decode(base64_string)

        if "verify_" in message.text:
            _, token = message.text.split("_", 1)
            if verify_status['verify_token'] != token:
                return await message.reply("⚠️ YOUR TOKEN IS INVALID or EXPIRED. TRY AGAIN BY CLICKING /start")
            await update_verify_status(id, is_verified=True, verified_time=time.time())
            if verify_status["link"] == "":
                await message.reply(
                    "Your token successfully verified and valid for: 24 Hour", 
                    reply_markup=PREMIUM_BUTTON,
                    protect_content=False, 
                    quote=True
                )
        elif string.startswith("premium"):
            if not is_premium:
                # Notify user to get premium
                await message.reply("Buy premium to access this content\nTo Buy Contact @rohit_1888", reply_markup=PREMIUM_BUTTON2)
                return
            
            # Handle premium logic
            try:
                base64_string = text.split(" ", 1)[1]
            except:
                return
            string = await decode(base64_string)
            argument = string.split("-")
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                except:
                    return
                if start <= end:
                    ids = range(start, end + 1)
                else:
                    ids = []
                    i = start
                    while True:
                        ids.append(i)
                        i -= 1
                        if i < end:
                            break
            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except:
                    return
            temp_msg = await message.reply("Please wait...")
            try:
                messages = await get_messages(client, ids)
            except:
                await message.reply_text("Something went wrong..!") 
                return
            await temp_msg.delete()
            snt_msgs = []

            for msg in messages:
                original_caption = msg.caption.html if msg.caption else ""
                if CUSTOM_CAPTION:
                    caption = f"{original_caption}\n\n{CUSTOM_CAPTION}"
                else:
                    caption = original_caption

                if DISABLE_CHANNEL_BUTTON:
                    reply_markup = msg.reply_markup
                else:
                    reply_markup = None

                try:
                    snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    snt_msgs.append(snt_msg)
                except:
                    pass

            if SECONDS == 0:
                return

            notification_msg = await message.reply(f"<b>🌺 <u>Notice</u> 🌺</b>\n\n<b>This file will be deleted in {get_exp_time(SECONDS)}. Please save or forward it to your saved messages before it gets deleted.</b>")
            await asyncio.sleep(SECONDS)    
            for snt_msg in snt_msgs:    
                try:    
                    await snt_msg.delete()  
                except: 
                    pass    
            await notification_msg.edit("<b>Your file has been successfully deleted! 😼</b>")  
            return

        elif string.startswith("get"):
            if not is_premium:
                if not verify_status['is_verified']:
                    token = ''.join(random.choices(piroayush.ascii_letters + piroayush.digits, k=10))
                    await update_verify_status(id, verify_token=token, link="")
                    link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
                    btn = [
                        [InlineKeyboardButton("Click here", url=link), InlineKeyboardButton('How to use the bot', url=TUT_VID)],  # First row with two buttons
                        [InlineKeyboardButton('BUY PREMIUM', callback_data='buy_prem')]  # Second row with one button
                    ]
                    await message.reply(f"Your Ads token is expired or invalid. Please verify to access the files.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. If you pass 1 ad, you can use the bot for 24 Hours after passing the ad.", reply_markup=InlineKeyboardMarkup(btn), protect_content=False, quote=True)
                    return

            try:
                base64_string = text.split(" ", 1)[1]
            except:
                return
            string = await decode(base64_string)
            argument = string.split("-")
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                except:
                    return
                if start <= end:
                    ids = range(start, end + 1)
                else:
                    ids = []
                    i = start
                    while True:
                        ids.append(i)
                        i -= 1
                        if i < end:
                            break
            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except:
                    return
            temp_msg = await message.reply("Please wait...")
            try:
                messages = await get_messages(client, ids)
            except:
                await message.reply_text("Something went wrong..!") 
                return
            await temp_msg.delete()
            snt_msgs = []
            for msg in messages:
                original_caption = msg.caption.html if msg.caption else ""
                if CUSTOM_CAPTION:
                    caption = f"{original_caption}\n\n{CUSTOM_CAPTION}"
                else:
                    caption = original_caption

                if DISABLE_CHANNEL_BUTTON:
                    reply_markup = msg.reply_markup
                else:
                    reply_markup = None

                try:
                    snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    snt_msgs.append(snt_msg)
                except:
                    pass

            if SECONDS == 0:
                return

            notification_msg = await message.reply(f"<b>🌺 <u>Notice</u> 🌺</b>\n\n<b>This file will be deleted in {get_exp_time(SECONDS)}. Please save or forward it to your saved messages before it gets deleted.</b>")
            await asyncio.sleep(SECONDS)    
            for snt_msg in snt_msgs:    
                try:    
                    await snt_msg.delete()  
                except: 
                    pass    
            await notification_msg.edit("<b>Your file has been successfully deleted! 😼</b>")  
            return
    else:
        try:
            reply_markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("😊 About Me", callback_data="about"), InlineKeyboardButton("🔒 Close", callback_data="close")],
                    [InlineKeyboardButton('BUY PREMIUM', callback_data='buy_prem')]
                ]
            )
            await message.reply_photo(
                photo=START_PIC,
                caption=START_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=message.from_user.id
                ),
                reply_markup=reply_markup,
            )
        except Exception as e:
            print(e)


#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

#=====================================================================================##

    
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ", url=client.invitelink),
            InlineKeyboardButton(text="ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ •", url=client.invitelink2),
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply_photo(
       photo = FORCE_PIC,
        caption = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

@Bot.on_message(filters.private & filters.command('addpaid') & filters.user(ADMINS))
async def add_premium_user_command(client, msg):
    if len(msg.command) != 3:
        await msg.reply_text("Usage: /addpaid <user_id> <time_limit_minutes>")
        return
    
    try:
        user_id = int(msg.command[1])
        time_limit_minutes = int(msg.command[2])
        
        await add_premium(user_id, time_limit_minutes)
        
        await msg.reply_text(
            f"User {user_id} added as a premium user for {time_limit_minutes} minutes."
        )
        await client.send_message(
            chat_id=user_id,
            text=f"🎉 Congratulations! You have been upgraded to premium for {time_limit_minutes} minutes.",
        )
    except ValueError:
        await msg.reply_text("Invalid user_id or time_limit_minutes. Please recheck.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {str(e)}")



# Command to remove premium user
@Bot.on_message(filters.private & filters.command('removepaid') & filters.user(ADMINS))
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("Usage: /removepaid <user_id>")
        return

    try:
        user_id = int(msg.command[1])

        # Fetch user info
        user_info = await collection.find_one({"user_id": user_id})
        if not user_info:
            await msg.reply_text(f"User {user_id} is not in the database.")
            return

        # Check if user is expired
        current_time = time.time()
        expiration_time = float(user_info["expiration_timestamp"])

        if expiration_time < current_time:
            # If expired, remove the user automatically
            await remove_premium(user_id)
            await msg.reply_text(f"User {user_id}'s premium had already expired and was automatically removed.")
        else:
            # If not expired, remove manually
            await remove_premium(user_id)
            await msg.reply_text(f"User {user_id} has been successfully removed from premium.")
    except ValueError:
        await msg.reply_text("Invalid user ID. Please provide a valid integer.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {str(e)}")

@Bot.on_message(filters.private & filters.command('listpaid') & filters.user(ADMINS))
async def list_premium_users_command(client, message):
    premium_users = collection.find({})
    premium_user_list = ['Active Premium Users in database:']
    current_time = time.time()

    async for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = float(user["expiration_timestamp"])

        if expiration_timestamp < current_time:
            # Remove expired users from the database
            await collection.delete_one({"user_id": user_id})
            continue  # Skip to the next user if this one is expired

        try:
            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "No Username"
            first_name = user_info.first_name

            # Calculate remaining time
            expiration_time = datetime.fromtimestamp(expiration_timestamp)
            remaining_time = expiration_time - datetime.now()

            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username}\n"
                f"Name: <code>{first_name}</code>\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"Error: Unable to fetch user details ({str(e)})"
            )

    if len(premium_user_list) == 1:  # No active users found
        await message.reply_text("I found 0 active premium users in my DB")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

