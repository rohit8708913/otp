import traceback
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import APP_ID, API_HASH, ADMINS
from database.database import *

SESSION_STRING_SIZE = 351

@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('login'))
async def login(bot: Client, message: Message):
    user_id = message.from_user.id
    user_sessions = await db.get_sessions(user_id)

    if len(user_sessions) >= 3:  # Set a session limit (change as needed)
        return await message.reply("⚠️ You have reached the maximum session limit. Remove an old session before adding a new one.")

    phone_number_msg = await bot.ask(user_id, "<b>Send your phone number including the country code.</b>\nExample: <code>+13124562345, +9171828181889</code>")
    if phone_number_msg.text == '/cancel':
        return await phone_number_msg.reply('<b>Process cancelled!</b>')

    phone_number = phone_number_msg.text
    client = Client(":memory:", APP_ID, API_HASH)
    await client.connect()
    await phone_number_msg.reply("Sending OTP...")

    try:
        code = await client.send_code(phone_number)
        phone_code_msg = await bot.ask(user_id, "Enter the OTP as `1 2 3 4 5`.\nType /cancel to cancel.", filters=filters.text, timeout=600)
    except PhoneNumberInvalid:
        return await phone_number_msg.reply('⚠️ Invalid phone number.')

    if phone_code_msg.text == '/cancel':
        return await phone_code_msg.reply('<b>Process cancelled!</b>')

    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        return await phone_code_msg.reply('⚠️ Invalid OTP.')
    except PhoneCodeExpired:
        return await phone_code_msg.reply('⚠️ OTP expired.')
    except SessionPasswordNeeded:
        password_msg = await bot.ask(user_id, 'Enter your two-step verification password.\nType /cancel to cancel.', filters=filters.text, timeout=300)
        if password_msg.text == '/cancel':
            return await password_msg.reply('<b>Process cancelled!</b>')
        try:
            await client.check_password(password_msg.text)
        except PasswordHashInvalid:
            return await password_msg.reply('⚠️ Incorrect password.')

    session_string = await client.export_session_string()
    await client.disconnect()

    if len(session_string) < SESSION_STRING_SIZE:
        return await message.reply('<b>Invalid session string.</b>')

    try:
        await db.add_session(user_id, session_string)
    except Exception as e:
        return await message.reply(f"⚠️ Error in login: `{e}`")

    await bot.send_message(user_id, "<b>Account logged in successfully.\nUse /session to view all your sessions.</b>")


@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('session'))
async def session_info(client, message):
    user_id = message.from_user.id
    user_sessions = await db.get_sessions(user_id)

    if not user_sessions:
        return await message.reply("⚠️ You have no active sessions. Use /login to add a session.")

    text = "Your Active Sessions:\n"
    for i, session in enumerate(user_sessions, 1):
        try:
            uclient = Client(":memory:", session_string=session, api_id=APP_ID, api_hash=API_HASH)
            await uclient.connect()
            me = await uclient.get_me()
            phone_number = me.phone_number
            await uclient.disconnect()
            text += f"{i}. 📞 `{phone_number}`\n"
        except Exception as e:
            text += f"{i}. ❌ Error fetching phone number: {e}\n"

    await message.reply(text)

@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('logout'))
async def logout(bot, message):
    user_id = message.from_user.id
    user_sessions = await db.get_sessions(user_id)

    if not user_sessions:
        return await message.reply("⚠️ You have no active sessions.")

    session_text = "Select a session to remove:\n"
    buttons = []
    
    for i, session in enumerate(user_sessions, 1):
        try:
            uclient = Client(":memory:", session_string=session, api_id=APP_ID, api_hash=API_HASH)
            await uclient.connect()
            me = await uclient.get_me()
            phone_number = me.phone_number
            await uclient.disconnect()
            session_text += f"{i}. 📞 `{phone_number}`\n"
            buttons.append([InlineKeyboardButton(f"Logout {phone_number}", callback_data=f"logout_{i}")])
        except:
            session_text += f"{i}. ❌ *Error retrieving phone number*\n"
            buttons.append([InlineKeyboardButton(f"Logout Session {i}", callback_data=f"logout_{i}")])

    keyboard = InlineKeyboardMarkup(buttons)
    await message.reply(session_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"logout_(\d+)"))
async def handle_logout_callback(bot, query):
    user_id = query.from_user.id
    session_index = int(query.matches[0].group(1)) - 1

    user_sessions = await db.get_sessions(user_id)
    if session_index >= len(user_sessions):
        return await query.answer("⚠️ Invalid session selection.", show_alert=True)

    session_to_remove = user_sessions[session_index]
    await db.remove_session(user_id, session_to_remove)
    await query.message.edit_text("✅ Session removed successfully!")


@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('otp'))
async def get_otp(client, message):
    user_id = message.from_user.id
    user_sessions = await db.get_sessions(user_id)

    if not user_sessions:
        return await message.reply("⚠️ You have no active sessions. Use /login to add a session.")

    text = "Select a session to receive the Telegram login OTP:\n"
    buttons = []

    for i, session in enumerate(user_sessions, 1):
        try:
            # Connect to session and get phone number
            uclient = Client(":memory:", session_string=session, api_id=APP_ID, api_hash=API_HASH)
            await uclient.connect()
            me = await uclient.get_me()
            phone_number = me.phone_number
            await uclient.disconnect()

            # Send OTP for login
            otp_client = Client(":memory:", api_id=APP_ID, api_hash=API_HASH)
            await otp_client.connect()
            code = await otp_client.send_code(phone_number)
            await otp_client.disconnect()

            text += f"{i}. 📞 `{phone_number}` ✅ OTP Sent\n"
            buttons.append([InlineKeyboardButton(f"Resend OTP for {phone_number}", callback_data=f"get_otp_{i}")])

            # Send OTP to the user
            await message.reply(f"🔑 Your Telegram login OTP for `{phone_number}`: `{code.phone_code_hash}`")

        except Exception as e:
            text += f"{i}. ❌ Error fetching OTP: {e}\n"

    # Check if there are valid buttons before sending inline keyboard
    if buttons:
        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply(text, reply_markup=keyboard)
    else:
        await message.reply("⚠️ No valid sessions available. Please check your saved sessions and try again.")