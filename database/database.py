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
        """Add a new session string along with the phone number for the user."""
        session_data = {"session": session, "phone_number": phone_number}  # Store both session and phone number
        await self.user_data.update_one(
            {'_id': user_id},
            {'$push': {'sessions': session_data}},  # Push as an object, not a plain string
            upsert=True
        )

    async def get_sessions(self, user_id: int):
        """Retrieve all stored sessions for a user."""
        user_data = await self.user_data.find_one({'_id': user_id})
        return user_data.get('sessions', []) if user_data else []

    async def remove_session(self, user_id: int, session: str):
        """Remove a specific session for the user."""
        await self.user_data.update_one(
            {'_id': user_id},
            {'$pull': {'sessions': {'session': session}}}  # Remove only the matching session
        )

# Initialize the database connection
db = Rohit(DB_URI, DB_NAME)