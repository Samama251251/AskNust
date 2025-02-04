from typing import Optional, List
from models.user import UserInDB, UserCreate
from config.database import Database
from datetime import datetime

class UserRepository:
    def __init__(self):
        self.db = Database.get_db()
        self.collection = self.db.users

    async def create_user(self, user: UserCreate) -> UserInDB:
        user_dict = user.dict()
        user_dict["hashed_password"] = user_dict.pop("password")  # Replace with proper hashing
        user_dict["created_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        return UserInDB(**user_dict)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        user = await self.collection.find_one({"_id": user_id})
        if user:
            user["_id"] = str(user["_id"])
            return UserInDB(**user)
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        user = await self.collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
            return UserInDB(**user)
        return None

    async def list_users(self, skip: int = 0, limit: int = 10) -> List[UserInDB]:
        users = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for user in cursor:
            user["_id"] = str(user["_id"])
            users.append(UserInDB(**user))
        return users

    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserInDB]:
        result = await self.collection.update_one(
            {"_id": user_id}, 
            {"$set": update_data}
        )
        if result.modified_count:
            return await self.get_user_by_id(user_id)
        return None

    async def delete_user(self, user_id: str) -> bool:
        result = await self.collection.delete_one({"_id": user_id})
        return result.deleted_count > 0 