import time
import logging
from datetime import datetime, timedelta
import motor, asyncio
import pymongo, os
from config import DB_URI, DB_NAME
import motor.motor_asyncio  # Import the correct module

logging.basicConfig(level=logging.INFO)

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

class Rohit:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]
        self.user_data = self.database['users']
        
    # USER MANAGEMENT
    async def present_user(self, user_id: int):
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        await self.user_data.insert_one({'_id': user_id})
        return

    async def full_userbase(self):
        user_docs = await self.user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in user_docs]
        return user_ids

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})
        return

    async def add_session(self, user_id: int, session: str, phone_number: str):
        """Add a new session string with phone number for the user in the database."""
        await self.user_data.update_one(
            {'_id': user_id},
            {'$push': {'sessions': {'session': session, 'phone_number': phone_number}}},  # Store both
            upsert=True
        )

    async def get_sessions(self, user_id: int):
        """Retrieve all session details (session string + phone number) for the user."""
        user = await self.user_data.find_one({'_id': user_id})
        if user:
            return user.get('sessions', [])
        return []

    async def remove_session(self, user_id: int, session: str):
        """Remove a specific session string from the user's session list."""
        await self.user_data.update_one(
            {'_id': user_id},
            {'$pull': {'sessions': {'session': session}}}  # Remove based on session string
        )


# Initialize the database connection
db = Rohit(DB_URI, DB_NAME)