from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from database.database import *
from pyrogram.errors import AuthKeyUnregistered

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "about":
        await query.message.edit_text(
            text=(
                f"<b>○ Creator : <a href='tg://user?id={OWNER_ID}'>Rohit</a>\n"
                f"○ Language : <code>Python3</code>\n"
                f"○ Library : <a href='https://docs.pyrogram.org/'>Pyrogram asyncio {__version__}</a>"
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
                f"📸 QR - ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ꜱᴄᴀɴ ({UPI_IMAGE_URL})\n\n"
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
        session_index = int(data.split("_")[1]) - 1
        user_sessions = await db.get_sessions(user_id)

        if session_index >= len(user_sessions):
            return await query.answer("⚠️ Invalid session selection.", show_alert=True)

        session_string = user_sessions[session_index]

        try:
            uclient = Client(":memory:", session_string=session_string, api_id=APP_ID, api_hash=API_HASH)
            await uclient.connect()

            me = await uclient.get_me()
            phone_number = me.phone_number

            async for msg in uclient.get_chat_history("Telegram", limit=5):
                if msg.unread and ("login code" in msg.text or "code" in msg.text):
                    otp_code = "".join(filter(str.isdigit, msg.text))
                    await query.message.reply(f"🔑 Your OTP for `{phone_number}`: `{otp_code}`")
                    await uclient.read_history("Telegram")  # Mark message as read
                    break

            await uclient.disconnect()
        except AuthKeyUnregistered:
            await db.remove_session(user_id, session_string)  # Remove expired session
            await query.answer("⚠️ Session expired. Please log in again.", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ Failed to fetch OTP: {e}", show_alert=True)