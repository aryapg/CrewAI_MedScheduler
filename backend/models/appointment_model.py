"""
Appointment data models.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AppointmentStatus(str, Enum):
    """Appointment status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class AppointmentCreate(BaseModel):
    """Model for creating a new appointment."""
    patient_id: str
    doctor_id: str
    doctor_name: str
    patient_name: str
    date: str  # ISO format date string
    time: str  # Time string (e.g., "10:30 AM")
    reason: Optional[str] = None
    specialty: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Model for updating an appointment."""
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Model for appointment response."""
    id: str
    patient_id: str
    doctor_id: str
    doctor_name: str
    patient_name: str
    date: str
    time: str
    status: AppointmentStatus
    reason: Optional[str] = None
    specialty: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    """Model for available appointment slots."""
    date: str
    time: str
    doctor_name: str
    doctor_id: str
    specialty: Optional[str] = None
    is_available: bool = True

