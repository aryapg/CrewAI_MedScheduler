"""
Authentication routes for user registration and login.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta, datetime
from backend.models.user_model import UserCreate, UserLogin, Token, UserResponse, UserRole
from backend.core.security import (
    verify_password, get_password_hash, create_access_token, get_current_user as get_current_user_dep
)
from backend.core.firestore_client import get_firestore
from backend.core.config import settings
from typing import Dict
import logging
from google.cloud import firestore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    Creates user in Firestore and returns JWT token.
    """
    db = get_firestore()
    
    try:
        # Check if user already exists
        users_ref = db.collection("users")
        existing_users = users_ref.where("email", "==", user_data.email).stream()
        
        if any(existing_users):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password_hash": hashed_password,
            "full_name": user_data.full_name,
            "role": user_data.role.value,
            "phone": user_data.phone,
            "specialty": user_data.specialty,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        
        # Add user to Firestore
        user_ref = users_ref.document()
        user_id = user_ref.id
        user_ref.set(user_doc)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "role": user_data.role.value},
            expires_delta=access_token_expires
        )
        
        # Return token and user info
        user_response = UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            phone=user_data.phone,
            specialty=user_data.specialty
        )
        
        logger.info(f"User registered: {user_data.email} (Role: {user_data.role.value})")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login an existing user.
    Validates credentials and returns JWT token.
    """
    db = get_firestore()
    
    try:
        # Find user by email
        users_ref = db.collection("users")
        user_query = users_ref.where("email", "==", credentials.email).limit(1).stream()
        
        user_doc = None
        user_id = None
        
        for doc in user_query:
            user_doc = doc.to_dict()
            user_id = doc.id
            break
        
        if not user_doc or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user_doc.get("password_hash", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        user_role = user_doc.get("role", "patient")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "role": user_role},
            expires_delta=access_token_expires
        )
        
        # Return token and user info
        user_response = UserResponse(
            id=user_id,
            email=user_doc.get("email", ""),
            full_name=user_doc.get("full_name", ""),
            role=UserRole(user_role),
            phone=user_doc.get("phone"),
            specialty=user_doc.get("specialty")
        )
        
        logger.info(f"User logged in: {credentials.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict = Depends(get_current_user_dep)):
    """
    Get current authenticated user information.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    
    try:
        user_doc = db.collection("users").document(user_id).get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user_doc.to_dict()
        
        return UserResponse(
            id=user_id,
            email=user_data.get("email", ""),
            full_name=user_data.get("full_name", ""),
            role=UserRole(user_data.get("role", "patient")),
            phone=user_data.get("phone"),
            specialty=user_data.get("specialty")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information"
        )

