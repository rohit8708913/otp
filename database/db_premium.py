


import time
import pymongo, os
from config import DB_URI, DB_NAME
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]
collection = database['premium-users']


# Remove expired users
async def remove_expired_users():
    current_time = datetime.now().isoformat()
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