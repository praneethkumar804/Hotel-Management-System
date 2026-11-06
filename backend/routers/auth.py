from fastapi import APIRouter, HTTPException, status

from backend.auth import verify_password
from backend.database import get_connection
from backend.schemas import LoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(payload: LoginRequest):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT user_id, username, password_hash FROM users WHERE username = ?",
            (payload.username,),
        ).fetchone()
    finally:
        connection.close()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return {"user_id": row["user_id"], "username": row["username"], "authenticated": True}