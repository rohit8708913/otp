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
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, TUT_VID, IS_VERIFY, VERIFY_EXPIRE, SHORTLINK_API, SHORTLINK_URL, PREMIUM_BUTTON, PREMIUM_BUTTON2
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import *
from database.db_premium import *
from config import *

"""add time in seconds for waiting before delete 
1 min = 60, 2 min = 60 × 2 = 120, 5 min = 60 × 5 = 300"""
SECONDS = int(os.getenv("SECONDS", "1200"))

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
                    "Your token successfully verified and valid for: 12 Hour", 
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

