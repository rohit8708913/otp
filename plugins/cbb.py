from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import *
from database.database import *


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔒 Close", callback_data="close")]]
            )
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
                    [
                        InlineKeyboardButton(
                            "Send Payment Screenshot(ADMIN) 📸", url=SCREENSHOT_URL
                        )
                    ],
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