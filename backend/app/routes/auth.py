"""
Routes d'authentification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.user_schema import (
    UserCreate, UserLogin, PhoneVerification,
    UserLoginResponse, UserResponse, TokenRefresh, TokenResponse
)
from app.services.auth_service import AuthService
from app.utils.security import create_access_token, create_refresh_token, verify_token

router = APIRouter()
auth_service = AuthService()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Inscription nouvel utilisateur"""
    user = await auth_service.register(db, user_data)
    return user

@router.post("/login", response_model=UserLoginResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Connexion utilisateur"""
    user = await auth_service.authenticate(db, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Numéro ou mot de passe incorrect"
        )
    
    tokens = await auth_service.create_tokens(user)
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
        "user": user
    }

@router.post("/verify-phone")
async def verify_phone(verification: PhoneVerification, db: Session = Depends(get_db)):
    """Vérification numéro de téléphone"""
    success = await auth_service.verify_phone(db, verification)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code de vérification invalide"
        )
    return {"message": "Téléphone vérifié avec succès"}

@router.post("/send-verification-code")
async def send_verification_code(phone_number: str, db: Session = Depends(get_db)):
    """Envoi code de vérification par SMS"""
    await auth_service.send_verification_code(db, phone_number)
    return {"message": "Code envoyé"}

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """Rafraîchir le token d'accès"""
    payload = verify_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )
    
    access_token = create_access_token(data={"sub": payload["sub"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(token: str = Depends(security)):
    """Déconnexion"""
    # Blacklister le token
    return {"message": "Déconnecté avec succès"}