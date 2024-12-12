import motor.motor_asyncio
from config import DB_URI, DB_NAME
from datetime import datetime

# Create an async client with Motor
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
collection = database['premium-users']

# Check if the user is a premium user
async def is_premium_user(user_id):
    user = await collection.find_one({"user_id": user_id})  # Async query
    return user is not None

# Remove premium user
async def remove_premium(user_id):
    await collection.delete_one({"user_id": user_id})  # Async removal

# Remove expired users
async def remove_expired_users():
    current_time = datetime.now().isoformat()
    await collection.delete_many({"expiration_timestamp": {"$lte": current_time}})  # Async removal

# Add premium user
async def add_premium(user_id, time_limit_minutes):
    expiration_time = datetime.now() + timedelta(minutes=time_limit_minutes)
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time.isoformat(),
    }
    await collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True
    )  # Async update

# List active premium users
async def list_premium_users():
    premium_users = collection.find({})
    premium_user_list = []

    async for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]
        expiration_time = datetime.fromisoformat(expiration_timestamp)
        remaining_time = expiration_time - datetime.now()

        if remaining_time.total_seconds() > 0:  # Only active users
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"
            premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info}")

    return premium_user_list