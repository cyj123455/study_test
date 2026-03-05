"""认证：注册、登录"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import get_password_hash, create_access_token, authenticate_user, get_user_by_username

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        role=UserRole.user.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(data={"sub": user.username})
    return Token(access_token=token, user=UserResponse.model_validate(user))

