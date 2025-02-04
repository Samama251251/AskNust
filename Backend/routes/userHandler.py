from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserResponse
from repositories.user_repository import UserRepository
from typing import List

router = APIRouter()
user_repository = UserRepository()

@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    existing_user = await user_repository.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = await user_repository.create_user(user)
    return UserResponse(
        id=created_user.id,
        email=created_user.email,
        name=created_user.name,
        created_at=created_user.created_at
    )

@router.get("/users/", response_model=List[UserResponse])
async def list_users(skip: int = 0, limit: int = 10):
    users = await user_repository.list_users(skip, limit)
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        ) for user in users
    ]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await user_repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at
    )