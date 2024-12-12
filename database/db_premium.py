import pymongo
from datetime import datetime, timedelta
from config import DB_URI, DB_NAME

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]
collection = database['premium-users']


def is_premium_user(user_id: int) -> bool:
    """Check if a user has an active premium subscription."""
    user = collection.find_one({"user_id": user_id})  # Use synchronous find_one
    if user:
        expiration_time = user.get("expiration_timestamp", 0)
        return time.time() < expiration_time
    return False

# Remove premium user with specified user_id
async def remove_premium(user_id):
    # Delete user from the collection by user_id (no need for await)
    collection.delete_one({"user_id": user_id})

# Remove expired users
async def remove_expired_users():
    current_time = datetime.now().isoformat()  # Get current time in ISO 8601 format
    # Delete all expired users based on the expiration_timestamp field (no need for await)
    collection.delete_many({"expiration_timestamp": {"$lte": current_time}})

# Add premium user
async def add_premium(user_id, time_limit_minutes):
    expiration_time = datetime.now() + timedelta(minutes=time_limit_minutes)
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time.isoformat(),  # Convert to ISO format
    }
    collection.update_one(
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