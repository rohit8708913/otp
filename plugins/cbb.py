from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from database.database import *
from pyrogram.errors import AuthKeyUnregistered, PeerIdInvalid
from pyrogram.raw import functions, types
import asyncio


@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "about":
        await query.message.edit_text(
            text=(
                f"<b>○ Creator : <a href='tg://user?id={OWNER_ID}'>Rohit</a>\n"
                f"○ Language : <code>Python3</code>\n"
                f"○ Library : <a href='https://docs.pyrogram.org/'>Pyrogram asyncio</a>"
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Close", callback_data="close")]])
        )

    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    elif data == "buy_prem":
        await query.message.delete()
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=QR_PIC,
            caption=(
                f"👋 {query.from_user.username}\n\n"
                f"🎖️ Available Plans :\n\n"
                f"● {PRICE1}  For 0 Days Prime Membership\n\n"
                f"● {PRICE2}  For 1 Month Prime Membership\n\n"
                f"● {PRICE3}  For 3 Months Prime Membership\n\n"
                f"● {PRICE4}  For 6 Months Prime Membership\n\n"
                f"● {PRICE5}  For 1 Year Prime Membership\n\n\n"
                f"💵 UPI ID -  <code>{UPI_ID}</code>\n\n\n"
                f"📸 QR - ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ꜱᴄᴀɴ\n\n"
                f"♻️ If payment is not getting sent on above given QR code then inform admin, he will give you new QR code\n\n\n"
                f"‼️ Must Send Screenshot after payment"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Send Payment Screenshot(ADMIN) 📸", url=SCREENSHOT_URL)],
                    [InlineKeyboardButton("🔒 Close", callback_data="close")],
                ]
            )
        )

    elif data.startswith("logout_"):
        session_index = int(data.split("_")[1]) - 1
        user_sessions = await db.get_sessions(user_id)

        if session_index >= len(user_sessions):
            return await query.answer("⚠️ Invalid session selection.", show_alert=True)

        session_to_remove = user_sessions[session_index]
        await db.remove_session(user_id, session_to_remove)
        await query.message.edit_text("✅ Session removed successfully!")

    elif data.startswith("fetch_otp_"):
        session_index = int(data.split("_")[-1]) - 1
        user_sessions = await db.get_sessions(user_id)

        if session_index >= len(user_sessions):
            return await query.answer("⚠️ Invalid session.", show_alert=True)

        session = user_sessions[session_index]
        possible_senders = ["+42777", "Telegram", "777000"]  

        try:
            uclient = Client(":memory:", session_string=session, api_id=APP_ID, api_hash=API_HASH)
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

            # **Step 2: Send a "hi" message to the OTP sender**
            hi_msg = await uclient.send_message("+42777", "hi")
            hi_timestamp = hi_msg.date  # Store the timestamp of "hi"

            await asyncio.sleep(5)  # Wait to allow OTP message to arrive

            # **Step 3: Fetch only messages AFTER "hi" was sent**
            latest_otp = None
            latest_time = None

            for sender in possible_senders:
                async for msg in uclient.get_chat_history(sender, limit=5):
                    if msg.date > hi_timestamp and "code" in msg.text.lower():
                        if not latest_time or msg.date > latest_time:
                            latest_time = msg.date
                            latest_otp = msg

            if latest_otp:
                await query.message.reply(f"📩 Latest OTP for `{phone_number}`:\n\n{latest_otp.text}")
                await uclient.read_history(latest_otp.chat.id)  # Mark as read
            else:
                await query.message.reply(f"⚠️ No new OTP messages found for `{phone_number}`.")

            await uclient.disconnect()
            await query.answer()  # Close loading animation

        except Exception as e:
            print(f"DEBUG: Error fetching OTP: {e}")
            await query.message.reply(f"⚠️ Couldn't fetch OTP for `{phone_number}`. Try logging in again.")
            await db.remove_session(user_id, session)  # Remove expired session