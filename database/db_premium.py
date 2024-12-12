


import time
import pymongo, os
from config import DB_URI, DB_NAME
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]
collection = database['premium-users']


async def add_premium(user_id, time_limit_minutes):
    # Validate the input time limit
    if time_limit_minutes <= 0:
        raise ValueError("Time limit must be greater than 0 minutes.")
    
    # Calculate expiration timestamp
    expiration_timestamp = int(time.time()) + time_limit_minutes * 60

    # Log expiration for debugging (optional)
    print(f"Adding user {user_id} with expiration timestamp {expiration_timestamp} "
          f"({datetime.fromtimestamp(expiration_timestamp)})")

    # Prepare data
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_timestamp,
    }

    # Insert or update the record in the database
    await collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True
    )

async def remove_expired_users():
    current_timestamp = int(time.time())

    expired_users = collection.find({"expiration_timestamp": {"$lte": current_timestamp}})
    
    for expired_user in expired_users:
        user_id = expired_user["user_id"]
        collection.delete_one({"user_id": user_id})

async def is_premium_user(user_id):
    user = collection.find_one({"user_id": user_id})
    return user is not None


