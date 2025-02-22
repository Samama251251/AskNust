import json
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from utils.auth import create_access_token
from repositories.user_repository import UserRepository

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserSignup(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

def get_user_repository(request: Request) -> UserRepository:
    # Retrieve the repository from the app state
    repository = request.app.state.user_repository
    if not repository:
        raise HTTPException(status_code=500, detail="Repository not initialized")
    return repository

@router.post("/signup")
async def signup(user: UserSignup, user_repo: UserRepository = Depends(get_user_repository)):
    existing_user = await user_repo.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = await user_repo.create_user(user)
    access_token = create_access_token({"email": created_user.email})
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "User created successfully",
            "user": {
                "id": str(created_user.id),
                "email": created_user.email,
                "name": created_user.name,
            },
            "access_token": access_token,
        }
    )

@router.post("/login")
async def login(request_data: LoginRequest, user_repo: UserRepository = Depends(get_user_repository)):
    user = await user_repo.get_user_by_email(request_data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not pwd_context.verify(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    access_token = create_access_token({"email": user.email})
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600  # 1 hour
    )
    return response

@router.post("/auth")
async def verify_auth(request: Request, user_repo: UserRepository = Depends(get_user_repository)):
    try:
        token = request.cookies.get("access_token")
        if not token:
            return JSONResponse(content={"isAuthenticated": False})
    
        payload = jwt.decode(token, "your-secret-key-here", algorithms=["HS256"])
        email = payload.get("email")
        if not email:
            return JSONResponse(content={"isAuthenticated": False})
    
        user = await user_repo.get_user_by_email(email)
        if not user:
            return JSONResponse(content={"isAuthenticated": False})
    
        return JSONResponse(content={"isAuthenticated": True})
    except JWTError:
        return JSONResponse(content={"isAuthenticated": False})