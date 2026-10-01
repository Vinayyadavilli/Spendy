from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_password_hash, verify_password, create_access_token
from ..core.dependencies import get_current_user
from ..models.user import User
from ..models.bank_account import BankAccount
from ..schemas.user_schema import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=new_user.id)
    return Token(access_token=token, user=UserResponse.model_validate(new_user))

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    
    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
