#Javpostr | @rohit_1888 on Tg
import asyncio
from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime, timedelta
import pytz  # For Indian Standard Time (IST)

from config import *
from dotenv import load_dotenv
from database.db_premium import remove_expired_users

from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv(".env")

def get_indian_time():
    """Returns the current time in IST."""
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)



class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = get_indian_time()  # Use IST for uptime tracking

        if FORCE_SUB_CHANNEL:
            try:
                link = await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                self.LOGGER(__name__).warning(
                    f"Please Double check the FORCE_SUB_CHANNEL value and Make sure Bot is Admin in channel with "
                    f"Invite Users via Link Permission, Current Force Sub Channel Value: {FORCE_SUB_CHANNEL}"
                )
                self.LOGGER(__name__).info("\nBot Stopped. @rohit_1888 for support")
                sys.exit()

        if FORCE_SUB_CHANNEL2:
            try:
                link = (await self.get_chat(FORCE_SUB_CHANNEL2)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCE_SUB_CHANNEL2)
                    link = (await self.get_chat(FORCE_SUB_CHANNEL2)).invite_link
                self.invitelink2 = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                self.LOGGER(__name__).warning(
                    f"Please Double check the FORCE_SUB_CHANNEL2 value and Make sure Bot is Admin in channel with "
                    f"Invite Users via Link Permission, Current Force Sub Channel Value: {FORCE_SUB_CHANNEL2}"
                )
                self.LOGGER(__name__).info("\nBot Stopped. Dm https://t.me/rohit_1888 for support")
                sys.exit()

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(
                f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {CHANNEL_ID}"
            )
            self.LOGGER(__name__).info("\nBot Stopped. @rohit_1888 for support")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot Started at {self.uptime.strftime('%Y-%m-%d %H:%M:%S')} IST")
        self.LOGGER(__name__).info(f"Bot Running..! Made by @rohit_1888")

        self.username = usr_bot_me.username

        # Web response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped. Made By @rohit_1888")


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(remove_expired_users, "interval", seconds=3600)
    scheduler.start()

    bot = Bot()
    await bot.start()

    # Keep the program running to let jobs execute
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())