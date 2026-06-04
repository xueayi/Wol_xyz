import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..auth import verify_password, hash_password, create_access_token, get_current_user
from ..schemas.auth import LoginRequest, TokenResponse, UserOut, PasswordChange, UsernameChange
from ..config import DATA_DIR

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.put("/password")
async def change_password(
    body: PasswordChange,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"success": True}


@router.put("/username")
async def change_username(
    body: UsernameChange,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="密码验证失败")
    existing = await db.execute(select(User).where(User.username == body.new_username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user.username = body.new_username
    await db.commit()
    token = create_access_token(data={"sub": user.username})
    return {"success": True, "access_token": token}


@router.post("/regenerate-secret")
async def regenerate_secret(user: User = Depends(get_current_user)):
    new_key = secrets.token_urlsafe(32)
    env_file = DATA_DIR / ".env"
    lines = []
    found = False
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("SECRET_KEY="):
                lines.append(f"SECRET_KEY={new_key}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"SECRET_KEY={new_key}")
    env_file.write_text("\n".join(lines) + "\n")
    return {"success": True, "message": "密钥已更新，请重启服务使其生效"}
