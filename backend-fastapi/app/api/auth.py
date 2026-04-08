from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, decode_token
)
from app.schemas.auth import RegisterRequest, TokenResponse, UserOut
import uuid

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def fetch_user_by_login(login: str):
    async with get_db() as db:
        return await db.fetchrow(
            """
            SELECT id, email, name, password_hash, created_at
            FROM users
            WHERE email = $1 OR name = $1
            LIMIT 1
            """,
            login,
        )


def build_token_response(user) -> dict:
    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access": token,
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user["id"]),
    }


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    async with get_db() as db:
        existing = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1", req.email
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

        user_id = str(uuid.uuid4())
        await db.execute(
            """
            INSERT INTO users (id, email, name, password_hash)
            VALUES ($1, $2, $3, $4)
            """,
            user_id, req.email, req.name, hash_password(req.password)
        )

    token = create_access_token({"sub": user_id, "email": req.email})
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = await fetch_user_by_login(form.username)
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="РќРµРІРµСЂРЅС‹Р№ email РёР»Рё РїР°СЂРѕР»СЊ")

    token_data = build_token_response(user)
    return TokenResponse(access_token=token_data["access_token"], token_type="bearer")

    async with get_db() as db:
        user = await db.fetchrow(
            "SELECT id, email, password_hash FROM users WHERE email = $1",
            form.username
        )
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login/", include_in_schema=False)
async def login_json(request: Request):
    data = await request.json()
    login_value = data.get("email") or data.get("username")
    password = data.get("password")
    user = await fetch_user_by_login(login_value or "")
    if not user or not password or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="РќРµРІРµСЂРЅС‹Р№ email РёР»Рё РїР°СЂРѕР»СЊ")
    return build_token_response(user)


@router.get("/me", response_model=UserOut)
@router.get("/me/", response_model=UserOut, include_in_schema=False)
async def me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    async with get_db() as db:
        user = await db.fetchrow(
            "SELECT id, email, name, created_at FROM users WHERE id = $1",
            payload["sub"]
        )
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return dict(user)


@router.get("/me/bookings")
@router.get("/me/bookings/", include_in_schema=False)
async def my_bookings(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    async with get_db() as db:
        rows = await db.fetch(
            """
            SELECT b.id, b.event_id, b.seat_id, b.status, b.created_at,
                   e.name as event_name, e.venue, e.date,
                   s.row, s.number, s.price
            FROM bookings b
            JOIN events e ON e.id = b.event_id
            JOIN seats s ON s.id = b.seat_id
            WHERE b.user_id = $1
            ORDER BY b.created_at DESC
            """,
            payload["sub"]
        )
    return [dict(r) for r in rows]
