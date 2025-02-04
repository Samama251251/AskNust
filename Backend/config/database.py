from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database_name = "askNustChatbot"  # Make it a class variable

    @classmethod
    async def connect_db(cls):
        try:
            # Use environment variables in production
            MONGODB_URL = "mongodb://localhost:27017/"
            cls.client = AsyncIOMotorClient(MONGODB_URL)
            
            # Verify connection
            await cls.client.admin.command('ping')
            print(f"Connected to MongoDB, using database: {cls.database_name}")
            
            # Initialize database
            return cls.client[cls.database_name]
        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
            raise e
        
    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            cls.client.close()

    @classmethod
    def get_db(cls):
        if cls.client is None:
            raise Exception("Database not initialized. Call connect_db() first")
        return cls.client[cls.database_name]