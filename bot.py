#Javpostr | @rohit_1888 on Tg
import asyncio
from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime, timedelta

from config import (
    API_HASH,
    APP_ID,
    LOGGER,
    TG_BOT_TOKEN,
    TG_BOT_WORKERS,
    FORCE_SUB_CHANNEL,
    CHANNEL_ID,
    PORT,
    FORCE_SUB_CHANNEL2
)
from dotenv import load_dotenv
from database.db_premium import remove_expired_users, collection

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables
load_dotenv(".env")

# Configuration for notifications
NOTIFICATION_CHECK_INTERVAL_SECONDS = 30
NOTIFICATION_TIME_BEFORE_EXPIRY_SECONDS = 60


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        if FORCE_SUB_CHANNEL:
            try:
                link = await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning(
                    "Bot can't Export Invite link from Force Sub Channel!"
                )
                self.LOGGER(__name__).info(
                    "\nBot Stopped. @rohit_1888 for support"
                )
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
                self.LOGGER(__name__).warning(
                    "Bot can't Export Invite link from Force Sub Channel!"
                )
                self.LOGGER(__name__).info(
                    "\nBot Stopped. @rohit_1888 for support"
                )
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
        self.LOGGER(__name__).info(f"Bot Running..! Made by @rohit_1888")
        self.username = usr_bot_me.username

        # Web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped. Made By @rohit_1888")


# Notify users whose subscriptions are about to expire
async def notify_expiring_users():
    """
    Checks the database for users whose subscriptions expire soon and notifies them.
    """
    current_time = datetime.now()
    notify_time = current_time + timedelta(seconds=NOTIFICATION_TIME_BEFORE_EXPIRY_SECONDS)

    expiring_users = collection.find({
        "expiration_timestamp": {"$lte": notify_time.isoformat(), "$gt": current_time.isoformat()}
    })

    for user in expiring_users:
        user_id = user["user_id"]
        expiration_time = datetime.fromisoformat(user["expiration_timestamp"])
        remaining_time = expiration_time - current_time

        try:
            # Notify the user
            async with Bot() as bot:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"⏳ Your premium subscription is expiring in "
                         f"{remaining_time.seconds} seconds! Renew now to continue enjoying premium benefits.",
                )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")


async def main():
    scheduler = AsyncIOScheduler()

    # Schedule the task to remove expired users every hour
    scheduler.add_job(remove_expired_users, "interval", seconds=3600)

    # Schedule the notification task
    scheduler.add_job(notify_expiring_users, "interval", seconds=NOTIFICATION_CHECK_INTERVAL_SECONDS)

    scheduler.start()

    # Start the bot
    bot = Bot()
    await bot.start()

    # Keep the program running to let jobs execute
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())