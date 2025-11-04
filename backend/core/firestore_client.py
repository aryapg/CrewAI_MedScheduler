"""
Firebase Admin SDK and Firestore client setup.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional
from backend.core.config import settings

# Global Firestore client
db: Optional[firestore.Client] = None


def initialize_firebase() -> firestore.Client:
    """
    Initialize Firebase Admin SDK and return Firestore client.
    Creates a temporary credentials file if private key is provided as string.
    """
    global db
    
    if db is not None:
        return db
    
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        db = firestore.client()
        return db
    except ValueError:
        # Not initialized, proceed with initialization
        pass
    
    # Method 1: Use credentials path if provided
    if settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
        db = firestore.client()
        return db
    
    # Method 2: Use private key from environment variables
    if settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
        # Create credentials dictionary from environment variables
        cred_dict = {
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key_id": "",
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{settings.FIREBASE_CLIENT_EMAIL}"
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
        db = firestore.client()
        return db
    
    # Method 3: Use default credentials (for local development)
    try:
        firebase_admin.initialize_app()
        db = firestore.client()
        return db
    except Exception as e:
        raise Exception(f"Failed to initialize Firebase: {str(e)}. Please provide FIREBASE_PRIVATE_KEY and FIREBASE_CLIENT_EMAIL or FIREBASE_CREDENTIALS_PATH")


def get_firestore() -> firestore.Client:
    """Get the Firestore client, initializing if necessary."""
    global db
    if db is None:
        db = initialize_firebase()
    return db

