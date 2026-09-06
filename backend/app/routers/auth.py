"""
Auth endpoints — officer registration/login backed by MongoDB.

    POST /api/v1/auth/register
    POST /api/v1/auth/login
    GET  /api/v1/auth/me        (requires Bearer token)
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import users_collection
from app.schemas import TokenResponse, UserLogin, UserPublic, UserRegister
from app.security import (
    JWTError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

bearer_scheme = HTTPBearer()


def _to_public(user_doc: dict) -> UserPublic:
    return UserPublic(
        id=str(user_doc["_id"]),
        name=user_doc["name"],
        email=user_doc["email"],
        officerId=user_doc["officerId"],
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency for protected routes — decodes the bearer token and
    loads the corresponding user from MongoDB."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise unauthorized

    user_id = payload.get("sub")
    if not user_id:
        raise unauthorized

    try:
        user_doc = await users_collection.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise unauthorized

    if user_doc is None:
        raise unauthorized

    return user_doc


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    existing = await users_collection.find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    existing_officer = await users_collection.find_one({"officerId": payload.officerId})
    if existing_officer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This officer ID is already registered.",
        )

    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "officerId": payload.officerId,
        "passwordHash": hash_password(payload.password),
    }
    result = await users_collection.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token({"sub": str(user_doc["_id"])})
    return TokenResponse(accessToken=token, user=_to_public(user_doc))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    invalid_creds = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    user_doc = await users_collection.find_one({"email": payload.email})
    if not user_doc or not verify_password(payload.password, user_doc["passwordHash"]):
        raise invalid_creds

    token = create_access_token({"sub": str(user_doc["_id"])})
    return TokenResponse(accessToken=token, user=_to_public(user_doc))


@router.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)):
    return _to_public(current_user)
