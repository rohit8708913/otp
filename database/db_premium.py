


import time
import pymongo, os
from config import DB_URI, DB_NAME


dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]
collection = database['premium-users']


async def add_premium(user_id, time_limit_minutes):
    try:
        # Validate and clamp `time_limit_minutes`
        if time_limit_minutes <= 0:
            raise ValueError("time_limit_minutes must be greater than 0")
        
        # Calculate expiration timestamp
        expiration_timestamp = int(time.time()) + time_limit_minutes * 60
        
        # Verify the computed timestamp is reasonable (e.g., within 1 year from now)
        current_year = datetime.now().year
        future_year = datetime.fromtimestamp(expiration_timestamp).year
        if future_year > current_year + 1:
            raise ValueError(f"Computed expiration timestamp is too large: {future_year}")
        
        # Prepare data for insertion/update
        premium_data = {
            "user_id": user_id,
            "expiration_timestamp": expiration_timestamp,
        }
        
        # Update or insert into the database
        await collection.update_one(
            {"user_id": user_id},
            {"$set": premium_data},
            upsert=True
        )
    except Exception as e:
        print(f"Error in add_premium: {e}")
async def remove_expired_users():
    current_timestamp = int(time.time())

    expired_users = collection.find({"expiration_timestamp": {"$lte": current_timestamp}})
    
    for expired_user in expired_users:
        user_id = expired_user["user_id"]
        collection.delete_one({"user_id": user_id})

async def is_premium_user(user_id):
    user = collection.find_one({"user_id": user_id})
    return user is not None


