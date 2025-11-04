"""
Questionnaire data models for pre-visit questionnaires.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class QuestionnaireSubmit(BaseModel):
    """Model for submitting a questionnaire."""
    appointment_id: str
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None
    allergies: Optional[str] = None
    additional_notes: Optional[str] = None


class QuestionnaireResponse(BaseModel):
    """Model for questionnaire response."""
    id: str
    appointment_id: str
    patient_id: str
    chief_complaint: Optional[str] = None
    symptoms: Optional[str] = None
    medical_history: Optional[str] = None
    current_medications: Optional[str] = None
    allergies: Optional[str] = None
    additional_notes: Optional[str] = None
    summary: Optional[str] = None
    submitted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

