import motor.motor_asyncio
from config import DB_URI, DB_NAME
from pytz import timezone
from datetime import datetime, timedelta

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



# List active premium users
async def list_premium_users():
    # Define IST timezone
    ist = timezone("Asia/Kolkata")

    # Fetch all premium users from the collection
    premium_users = collection.find({})
    premium_user_list = []

    async for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        # Convert expiration timestamp to a timezone-aware datetime object in IST
        expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)

        # Calculate the remaining time (make sure both are timezone-aware)
        remaining_time = expiration_time - datetime.now(ist)

        if remaining_time.total_seconds() > 0:  # Only active users
            # Calculate days, hours, minutes, and seconds left
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )

            # Format the expiration time in IST and remaining time
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            # Format the expiration time for clarity
            formatted_expiry_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')

            # Add user info to the list with both remaining and expiration times
            premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info} (Expires at {formatted_expiry_time})")

    return premium_user_list



# Add premium user
async def add_premium(user_id, time_value, time_unit):
    """
    Add a premium user for a specific duration in minutes or days.
    
    Args:
        user_id (int): The ID of the user to add premium access for.
        time_value (int): The numeric value of the duration.
        time_unit (str): The time unit - 'm' for minutes, 'd' for days.
    """
    # Get IST timezone
    ist = timezone("Asia/Kolkata")

    # Calculate expiration time based on the unit
    if time_unit == 'm':
        expiration_time = datetime.now(ist) + timedelta(minutes=time_value)
    elif time_unit == 'd':
        expiration_time = datetime.now(ist) + timedelta(days=time_value)
    else:
        raise ValueError("Invalid time unit. Use 'm' for minutes or 'd' for days.")

    # Prepare premium data
    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time.isoformat(),  # Store in ISO format
    }

    # Update the database or insert if user_id does not exist
    await collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True
    )  # Async update

    # Format the expiration time for easy reading in IST
    formatted_expiration_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')

    # Notify the user and admin (if needed) with activation and expiration times
    print(f"User {user_id} premium access expires on {formatted_expiration_time}")

    return formatted_expiration_time