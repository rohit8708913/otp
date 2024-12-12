#Don't remove This Line From Here. Tg: @im_piro | @PiroHackz



import time
import pymongo, os
from config import DB_URI, DB_NAME
from bot import Bot


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


# Add premium user with specified months
async def add_premium(user_id, time_limit_months):
    expiration_timestamp = int(time.time()) + time_limit_months * 30 * 24 * 60 * 60
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_timestamp,
    }
    await collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True  # Ensure it updates or inserts if not present
    )

# Remove premium user by user_id
async def remove_premium(user_id):
    await collection.delete_one({"user_id": user_id})

# Remove all expired users from the database
async def remove_expired_users():
    current_timestamp = int(time.time())
    await collection.delete_many({"expiration_timestamp": {"$lte": current_timestamp}})


# List all premium users in the database
async def list_premium_users():
    premium_users = collection.find({})
    premium_user_list = []

    async for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        # Calculate remaining time in seconds
        remaining_seconds = expiration_timestamp - time.time()

        if remaining_seconds > 0:
            remaining_days = int(remaining_seconds // (24 * 60 * 60))  # days
            remaining_hours = int((remaining_seconds % (24 * 60 * 60)) // 3600)  # hours
            remaining_minutes = int((remaining_seconds % 3600) // 60)  # minutes
            remaining_seconds = int(remaining_seconds % 60)  # seconds

            # Format remaining time in readable format
            expiry_info = f"{remaining_days}d {remaining_hours}h {remaining_minutes}m {remaining_seconds}s left"
        else:
            expiry_info = "Expired"

        premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info}")

    return premium_user_list


async def get_users_near_expiry(seconds):
    """Fetch users whose subscriptions will expire within the next `seconds`."""
    current_timestamp = int(time.time())
    near_expiry_timestamp = current_timestamp + seconds

    # Find users near expiry
    return await collection.find(
        {"expiration_timestamp": {"$lte": near_expiry_timestamp, "$gt": current_timestamp}}
    ).to_list(length=None)