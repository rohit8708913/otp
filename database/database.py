#Don't remove This Line From Here. Tg: @im_piro | @PiroHackz



import time
import pymongo, os
from config import DB_URI, DB_NAME
from bot import Bot
from datetime import datetime, timedelta

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



# Remove premium user with specified user_id
async def remove_premium(user_id):
    # Delete user from the collection by user_id
    await collection.delete_one({"user_id": user_id})



# Remove expired users
async def remove_expired_users():
    current_time = datetime.now().isoformat()  # Get current time in ISO 8601 format
    # Delete all expired users based on the expiration_timestamp field
    await collection.delete_many({"expiration_timestamp": {"$lte": current_time}})



# Add premium user
async def add_premium(user_id, time_limit_minutes):
    expiration_time = datetime.now() + timedelta(minutes=time_limit_minutes)
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time.isoformat(),  # Convert to ISO format
    }
    await collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True
    )

# List premium users
async def list_premium_users():
    premium_users = collection.find({})
    premium_user_list = []

    async for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        # Convert expiration_timestamp to datetime
        try:
            expiration_time = (
                datetime.fromisoformat(expiration_timestamp)
                if isinstance(expiration_timestamp, str)
                else datetime.fromtimestamp(expiration_timestamp)
            )
            remaining_time = expiration_time - datetime.now()

            if remaining_time.total_seconds() > 0:
                days, hours, minutes, seconds = (
                    remaining_time.days,
                    remaining_time.seconds // 3600,
                    (remaining_time.seconds // 60) % 60,
                    remaining_time.seconds % 60,
                )
                expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"
            else:
                expiry_info = "Expired"
        except Exception as e:
            expiry_info = f"Error: {e}"

        premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info}")

    return premium_user_list