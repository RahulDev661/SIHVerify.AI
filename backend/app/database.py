"""
MongoDB connection (Motor async client).

One client is created at import time and reused for the life of the
process — this is the standard pattern for Motor under FastAPI (the
client manages its own connection pool internally, so there's no need
to open/close per-request).
"""

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import MONGODB_DB_NAME, MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]

# Collections
users_collection = db["users"]
scan_history_collection = db["scan_history"]
