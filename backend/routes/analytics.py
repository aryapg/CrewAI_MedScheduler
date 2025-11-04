"""
Analytics routes for dashboard statistics and reports.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Optional
from datetime import datetime, timedelta
from backend.core.security import get_current_user, require_role
from backend.core.firestore_client import get_firestore
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get dashboard analytics based on user role.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        if user_role == "patient":
            return await _get_patient_analytics(db, user_id)
        elif user_role == "doctor":
            return await _get_doctor_analytics(db, user_id)
        elif user_role == "admin":
            return await _get_admin_analytics(db)
        else:
            return await _get_patient_analytics(db, user_id)
            
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics"
        )


async def _get_patient_analytics(db, user_id: str) -> Dict:
    """Get analytics for patient dashboard."""
    appointments_ref = db.collection("appointments")
    
    # Get all patient appointments
    appointments = appointments_ref.where("patient_id", "==", user_id).stream()
    
    total_appointments = 0
    confirmed_appointments = 0
    pending_appointments = 0
    upcoming_appointments = []
    
    today = datetime.utcnow().date()
    
    for appointment in appointments:
        total_appointments += 1
        appointment_data = appointment.to_dict()
        
        status = appointment_data.get("status", "pending")
        if status == "confirmed":
            confirmed_appointments += 1
        elif status == "pending":
            pending_appointments += 1
        
        # Check for upcoming appointments
        appointment_date_str = appointment_data.get("date", "")
        try:
            appointment_date = datetime.fromisoformat(appointment_date_str.replace("Z", "+00:00")).date()
            if appointment_date >= today:
                upcoming_appointments.append({
                    "id": appointment.id,
                    "doctor_name": appointment_data.get("doctor_name", ""),
                    "date": appointment_date_str,
                    "time": appointment_data.get("time", ""),
                    "status": status
                })
        except:
            pass
    
    # Get questionnaires
    questionnaires_ref = db.collection("questionnaires")
    questionnaires = questionnaires_ref.where("patient_id", "==", user_id).stream()
    total_questionnaires = sum(1 for _ in questionnaires)
    
    return {
        "total_appointments": total_appointments,
        "confirmed_appointments": confirmed_appointments,
        "pending_appointments": pending_appointments,
        "upcoming_appointments": upcoming_appointments[:5],  # Limit to 5
        "total_questionnaires": total_questionnaires
    }


async def _get_doctor_analytics(db, user_id: str) -> Dict:
    """Get analytics for doctor dashboard."""
    appointments_ref = db.collection("appointments")
    
    # Get all doctor appointments
    appointments = appointments_ref.where("doctor_id", "==", user_id).stream()
    
    total_appointments = 0
    today_appointments = 0
    pending_reviews = 0
    total_patients = set()
    today_schedule = []
    
    today = datetime.utcnow().date()
    
    for appointment in appointments:
        total_appointments += 1
        appointment_data = appointment.to_dict()
        
        patient_id = appointment_data.get("patient_id", "")
        if patient_id:
            total_patients.add(patient_id)
        
        # Check for today's appointments
        appointment_date_str = appointment_data.get("date", "")
        try:
            appointment_date = datetime.fromisoformat(appointment_date_str.replace("Z", "+00:00")).date()
            if appointment_date == today:
                today_appointments += 1
                today_schedule.append({
                    "id": appointment.id,
                    "patient_name": appointment_data.get("patient_name", ""),
                    "time": appointment_data.get("time", ""),
                    "status": appointment_data.get("status", "pending"),
                    "type": appointment_data.get("reason", "Consultation")
                })
        except:
            pass
        
        # Check for pending questionnaires
        if appointment_data.get("status") == "confirmed":
            questionnaires_ref = db.collection("questionnaires")
            questionnaire_query = questionnaires_ref.where("appointment_id", "==", appointment.id).limit(1).stream()
            has_questionnaire = any(questionnaire_query)
            if has_questionnaire:
                pending_reviews += 1
    
    return {
        "total_appointments": total_appointments,
        "today_appointments": today_appointments,
        "total_patients": len(total_patients),
        "pending_reviews": pending_reviews,
        "today_schedule": sorted(today_schedule, key=lambda x: x.get("time", ""))
    }


async def _get_admin_analytics(db) -> Dict:
    """Get analytics for admin dashboard."""
    appointments_ref = db.collection("appointments")
    users_ref = db.collection("users")
    
    # Get all appointments
    appointments = appointments_ref.stream()
    
    total_appointments = 0
    total_confirmed = 0
    total_pending = 0
    total_cancelled = 0
    
    for appointment in appointments:
        total_appointments += 1
        status = appointment.to_dict().get("status", "pending")
        if status == "confirmed":
            total_confirmed += 1
        elif status == "pending":
            total_pending += 1
        elif status == "cancelled":
            total_cancelled += 1
    
    # Get user counts
    users = users_ref.stream()
    total_users = 0
    total_patients = 0
    total_doctors = 0
    
    for user in users:
        total_users += 1
        role = user.to_dict().get("role", "patient")
        if role == "patient":
            total_patients += 1
        elif role == "doctor":
            total_doctors += 1
    
    # Get reminders
    reminders_ref = db.collection("reminders")
    reminders = reminders_ref.stream()
    total_reminders = sum(1 for _ in reminders)
    
    # Get questionnaires
    questionnaires_ref = db.collection("questionnaires")
    questionnaires = questionnaires_ref.stream()
    total_questionnaires = sum(1 for _ in questionnaires)
    
    return {
        "total_appointments": total_appointments,
        "total_confirmed": total_confirmed,
        "total_pending": total_pending,
        "total_cancelled": total_cancelled,
        "total_users": total_users,
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_reminders": total_reminders,
        "total_questionnaires": total_questionnaires
    }


@router.get("/stats")
async def get_stats(
    days: Optional[int] = 30,
    current_user: Dict = Depends(require_role(["doctor", "admin"]))
):
    """
    Get detailed statistics for doctors and admins.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        appointments_ref = db.collection("appointments")
        
        if user_role == "doctor":
            query = appointments_ref.where("doctor_id", "==", user_id)
        else:
            query = appointments_ref
        
        appointments = query.stream()
        
        stats = {
            "period_days": days,
            "total_appointments": 0,
            "by_status": {
                "confirmed": 0,
                "pending": 0,
                "cancelled": 0,
                "completed": 0
            },
            "by_specialty": {}
        }
        
        for appointment in appointments:
            appointment_data = appointment.to_dict()
            created_at = appointment_data.get("created_at")
            
            # Filter by date if possible
            if created_at and isinstance(created_at, datetime) and created_at >= start_date:
                stats["total_appointments"] += 1
                status = appointment_data.get("status", "pending")
                if status in stats["by_status"]:
                    stats["by_status"][status] += 1
                
                specialty = appointment_data.get("specialty", "General")
                stats["by_specialty"][specialty] = stats["by_specialty"].get(specialty, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )

