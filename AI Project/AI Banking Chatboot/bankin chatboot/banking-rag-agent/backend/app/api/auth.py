"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status

from app.auth.security import create_access_token, hash_password, verify_password
from app.database.mongodb import get_collection
from app.schemas.schemas import TokenResponse, UserLogin, UserRegister, UserResponse, UserRole
from app.utils.helpers import generate_id, utc_now

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    users = get_collection("users")
    existing = await users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user_id = generate_id("usr_")
    user_doc = {
        "_id": user_id,
        "name": payload.name,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "role": UserRole.CUSTOMER.value,
        "created_at": utc_now(),
    }
    await users.insert_one(user_doc)

    token = create_access_token({"sub": user_id, "role": user_doc["role"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, name=payload.name, email=payload.email.lower(), role=UserRole.CUSTOMER),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    user = await get_collection("users").find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": user["_id"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["_id"],
            name=user["name"],
            email=user["email"],
            role=UserRole(user["role"]),
        ),
    )
