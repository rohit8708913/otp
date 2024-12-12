#Don't remove This Line From Here. Tg: @im_piro | @PiroHackz



import time
import asyncio
import pymongo, os
from config import DB_URI, DB_NAME
from bot import Bot
from datetime import datetime, timedelta
from asyncio import sleep

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]


user_data = database['users']
collection = database['premium-users']

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }


async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    user_data.insert_one(user)
    return

async def db_verify_status(user_id):
    user = user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

# Check if a user is a premium user
def is_premium_user(user_id):
    user = collection.find_one({"user_id": user_id})
    return user is not None

# Remove premium user by user_id
def remove_premium(user_id):
    collection.delete_one({"user_id": user_id})

# Remove expired premium users
def remove_expired_users():
    current_time = datetime.now()  # Current datetime object
    collection.delete_many({"expiration_timestamp": {"$lte": current_time}})

# Add a premium user with expiration time
def add_premium(user_id, time_limit_minutes):
    expiration_time = datetime.now() + timedelta(minutes=time_limit_minutes)
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time,  # Store datetime object directly
    }
    collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True
    )

# List premium users with their remaining time, excluding expired ones
async def list_premium_users():
    # Use asyncio.to_thread to run the blocking code in a separate thread
    premium_users = await asyncio.to_thread(list, collection.find({}))
    premium_user_list = []

    for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        # Check if expiration_timestamp is a datetime object, convert if needed
        if isinstance(expiration_timestamp, str):
            expiration_time = datetime.fromisoformat(expiration_timestamp)
        else:
            expiration_time = expiration_timestamp  # Already a datetime object

        # Calculate remaining time
        remaining_time = expiration_time - datetime.now()

        if remaining_time.total_seconds() > 0:
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"
            premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info}")
        # Expired users will be excluded, so no action for them

    if not premium_user_list:
        return "No active premium users found."
