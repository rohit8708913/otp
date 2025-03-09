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
from pyrogram.raw import functions, types
import asyncio
from pyrogram.errors import AuthKeyUnregistered, PeerIdInvalid

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


@Client.on_message(filters.private & filters.user(ADMINS) & filters.command('otp'))
async def get_otp(client, message):
    user_id = message.from_user.id
    user_sessions = await db.get_sessions(user_id)

    if not user_sessions:
        return await message.reply("⚠️ You have no active sessions. Use /login to add a session.")

    text = "🔹 **Your Active Sessions:**\n\n"
    buttons = []

    for i, session in enumerate(user_sessions, 1):
        try:
            uclient = Client(":memory:", session_string=session, api_id=APP_ID, api_hash=API_HASH)
            await uclient.connect()
            me = await uclient.get_me()
            phone_number = me.phone_number

            text += f"{i}. 📞 `{phone_number}`\n"
            buttons.append([InlineKeyboardButton(f"Get OTP for {phone_number}", callback_data=f"fetch_otp_{i}")])

            await uclient.disconnect()
        except Exception as e:
            print(f"DEBUG: Error in session {i}: {e}")

    keyboard = InlineKeyboardMarkup(buttons)
    await message.reply(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"fetch_otp_(\d+)"))
async def fetch_otp_callback(client, query):
    user_id = query.from_user.id
    session_index = int(query.matches[0].group(1)) - 1
    user_sessions = await db.get_sessions(user_id)

    if session_index >= len(user_sessions):
        return await query.answer("⚠️ No valid session found.", show_alert=True)

    session_string = user_sessions[session_index]

    try:
        uclient = Client(":memory:", session_string=session_string, api_id=APP_ID, api_hash=API_HASH)
        await uclient.connect()
        me = await uclient.get_me()
        phone_number = me.phone_number

        # **Step 1: Add Peer as Contact**
        await uclient.invoke(
            functions.contacts.ImportContacts(
                contacts=[
                    types.InputPhoneContact(
                        client_id=0, phone="+42777", first_name="Telegram", last_name="OTP"
                    )
                ]
            )
        )

        # **Step 2: Send "hi" to introduce peer**
        await uclient.send_message("+42777", "hi")
        await asyncio.sleep(5)  # Wait for OTP to arrive

        # **Step 3: Fetch latest OTP**
        latest_otp = None
        latest_time = None
        possible_senders = ["+42777", "Telegram", "777000"]

        for sender in possible_senders:
            async for msg in uclient.get_chat_history(sender, limit=5):
                if msg.text and "code" in msg.text:
                    if not latest_time or msg.date > latest_time:
                        latest_time = msg.date
                        latest_otp = msg

        if latest_otp:
            await query.message.reply(f"📩 **Latest OTP for `{phone_number}`:**\n\n{latest_otp.text}")
            await uclient.read_history(latest_otp.chat.id)  # Mark as read
        else:
            await query.answer(f"⚠️ No new OTP messages found for `{phone_number}`.", show_alert=True)

        await uclient.disconnect()

    except AuthKeyUnregistered:
        await db.remove_session(user_id, session_string)  # Remove expired session
        await query.answer("⚠️ Session expired. Please log in again.", show_alert=True)
    except PeerIdInvalid:
        await query.answer("⚠️ Cannot access OTP messages. Try again later.", show_alert=True)
    except Exception as e:
        await query.answer(f"❌ Error fetching OTP: {e}", show_alert=True)