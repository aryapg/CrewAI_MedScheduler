"""
Reminder routes for scheduling and managing appointment reminders.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.core.security import get_current_user
from backend.core.firestore_client import get_firestore
from backend.agents.reminder_agent import (
    schedule_reminder as agent_schedule,
    send_immediate_reminder as agent_send_immediate
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminder", tags=["Reminders"])


class ScheduleReminderRequest(BaseModel):
    """Request model for scheduling reminder."""
    appointment_id: str
    reminder_type: str = "sms"
    hours_before: int = 24


@router.post("/schedule", status_code=status.HTTP_201_CREATED)
async def schedule_reminder(
    request: ScheduleReminderRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Schedule a reminder for an appointment.
    Triggers reminder agent and stores reminder in Firestore.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    
    try:
        # Get appointment
        appointment_ref = db.collection("appointments").document(request.appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        appointment_data = appointment_doc.to_dict()
        
        # Get patient contact info for reminder
        patient_id = appointment_data.get("patient_id", "")
        patient_email = ""
        patient_phone = ""
        
        if patient_id:
            try:
                patient_doc = db.collection("users").document(patient_id).get()
                if patient_doc.exists:
                    patient_data = patient_doc.to_dict()
                    patient_email = patient_data.get("email", "")
                    patient_phone = patient_data.get("phone", "")
            except Exception as e:
                logger.warning(f"Could not fetch patient contact info: {str(e)}")
        
        # Check permissions
        if (current_user["role"] not in ["doctor", "admin"] and 
            appointment_data["patient_id"] != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to schedule reminders for this appointment"
            )
        
        # Validate reminder type
        reminder_type = request.reminder_type
        if reminder_type not in ["sms", "email"]:
            reminder_type = "sms"
        
        # Trigger reminder agent
        agent_result = agent_schedule(
            appointment_id=request.appointment_id,
            patient_name=appointment_data.get("patient_name", ""),
            doctor_name=appointment_data.get("doctor_name", ""),
            appointment_date=appointment_data.get("date", ""),
            appointment_time=appointment_data.get("time", ""),
            reminder_type=reminder_type,
            hours_before=request.hours_before
        )
        
        logger.info(f"Reminder agent result: {agent_result}")
        
        # Compute scheduled_at = appointment_datetime - hours_before
        try:
            from datetime import datetime as dt, timezone, timedelta
            appt_date_str = appointment_data.get("date", "")  # YYYY-MM-DD
            appt_time_str = appointment_data.get("time", "")  # e.g., "10:00 AM"
            # Parse time
            time_parts = appt_time_str.strip().split(" ")
            hh_mm = time_parts[0]
            am_pm = (time_parts[1] if len(time_parts) > 1 else "AM").upper()
            hour, minute = [int(x) for x in hh_mm.split(":")]
            if am_pm == "PM" and hour != 12:
                hour += 12
            if am_pm == "AM" and hour == 12:
                hour = 0
            appt_dt_naive = dt.strptime(appt_date_str, "%Y-%m-%d").replace(hour=hour, minute=minute)
            # Treat as UTC for simplicity in local dev
            appt_dt = appt_dt_naive.replace(tzinfo=timezone.utc)
            scheduled_at = appt_dt - timedelta(hours=request.hours_before)
        except Exception:
            # Fallback: schedule immediately
            from datetime import datetime as dt, timezone
            scheduled_at = dt.now(timezone.utc)

        # Store reminder in Firestore
        reminder_doc = {
            "appointment_id": request.appointment_id,
            "patient_id": appointment_data.get("patient_id", ""),
            "doctor_id": appointment_data.get("doctor_id", ""),
            "reminder_type": reminder_type,
            "hours_before": request.hours_before,
            "status": "scheduled",
            "scheduled_at": scheduled_at,
            "appointment_date": appointment_data.get("date", ""),
            "appointment_time": appointment_data.get("time", ""),
            "created_by": user_id
        }
        
        reminders_ref = db.collection("reminders")
        reminder_ref = reminders_ref.document()
        reminder_id = reminder_ref.id
        reminder_ref.set(reminder_doc)
        
        logger.info(f"Reminder scheduled: {reminder_id}")
        
        # Send immediately only if scheduled time has already passed
        try:
            from backend.core.email_service import send_appointment_reminder
            from datetime import datetime as dt, timezone
            now_utc = dt.now(timezone.utc)
            if patient_email and scheduled_at <= now_utc:
                # Small delay to ensure confirmation email is delivered first
                try:
                    import asyncio
                    await asyncio.sleep(2)
                except Exception:
                    pass
                send_appointment_reminder(
                    patient_email=patient_email,
                    patient_name=appointment_data.get("patient_name", ""),
                    doctor_name=appointment_data.get("doctor_name", ""),
                    appointment_date=appointment_data.get("date", ""),
                    appointment_time=appointment_data.get("time", ""),
                    specialty=appointment_data.get("specialty", "General"),
                    reason=appointment_data.get("reason")
                )
                logger.info(f"Reminder email sent immediately to {patient_email} for appointment on {appointment_data.get('date')} (with Gemini-generated content)")
        except Exception as e:
            logger.error(f"Failed to send reminder email: {str(e)}")
        
        return {
            "message": "Reminder scheduled successfully",
            "reminder_id": reminder_id,
            "agent_result": agent_result,
            "reminder_details": {
                "type": reminder_type,
                "hours_before": request.hours_before,
                "scheduled_at": reminder_doc["scheduled_at"].isoformat(),
                "appointment_date": appointment_data.get("date", ""),
                "appointment_time": appointment_data.get("time", ""),
                "patient_email": patient_email,
                "patient_phone": patient_phone,
                "contact_info": f"Email: {patient_email or 'Not provided'} | Phone: {patient_phone or 'Not provided'}"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule reminder: {str(e)}"
        )


@router.post("/send", status_code=status.HTTP_200_OK)
async def send_immediate_reminder(
    appointment_id: str,
    reminder_type: str = "sms",
    current_user: Dict = Depends(get_current_user)
):
    """
    Send an immediate reminder for an appointment.
    Triggers reminder agent and logs the reminder.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    
    try:
        # Get appointment
        appointment_ref = db.collection("appointments").document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        appointment_data = appointment_doc.to_dict()
        
        # Check permissions
        if (current_user["role"] not in ["doctor", "admin"] and 
            appointment_data["patient_id"] != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to send reminders for this appointment"
            )
        
        # Validate reminder type
        if reminder_type not in ["sms", "email"]:
            reminder_type = "sms"
        
        # Trigger reminder agent
        agent_result = agent_send_immediate(
            appointment_id=appointment_id,
            patient_name=appointment_data.get("patient_name", ""),
            doctor_name=appointment_data.get("doctor_name", ""),
            appointment_date=appointment_data.get("date", ""),
            appointment_time=appointment_data.get("time", ""),
            reminder_type=reminder_type
        )
        
        logger.info(f"Immediate reminder agent result: {agent_result}")
        
        # Store reminder log in Firestore
        reminder_doc = {
            "appointment_id": appointment_id,
            "patient_id": appointment_data.get("patient_id", ""),
            "doctor_id": appointment_data.get("doctor_id", ""),
            "reminder_type": reminder_type,
            "status": "sent",
            "sent_at": datetime.utcnow(),
            "appointment_date": appointment_data.get("date", ""),
            "appointment_time": appointment_data.get("time", ""),
            "created_by": user_id,
            "immediate": True
        }
        
        reminders_ref = db.collection("reminders")
        reminder_ref = reminders_ref.document()
        reminder_id = reminder_ref.id
        reminder_ref.set(reminder_doc)
        
        logger.info(f"Immediate reminder sent: {reminder_id}")
        
        return {
            "message": "Reminder sent successfully",
            "reminder_id": reminder_id,
            "agent_result": agent_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send reminder: {str(e)}"
        )


@router.get("/logs", status_code=status.HTTP_200_OK)
async def get_reminder_logs(
    appointment_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get reminder logs.
    Returns all reminders for appointments accessible by the current user.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        reminders_ref = db.collection("reminders")
        
        # Filter by appointment if provided
        if appointment_id:
            query = reminders_ref.where("appointment_id", "==", appointment_id)
        else:
            # Filter by user role
            if user_role == "patient":
                query = reminders_ref.where("patient_id", "==", user_id)
            elif user_role == "doctor":
                query = reminders_ref.where("doctor_id", "==", user_id)
            elif user_role == "admin":
                query = reminders_ref  # Admins see all
            else:
                query = reminders_ref.where("patient_id", "==", user_id)
        
        reminders = []
        for doc in query.order_by("scheduled_at", direction="DESCENDING").limit(50).stream():
            reminder_data = doc.to_dict()
            reminders.append({
                "id": doc.id,
                **reminder_data,
                "scheduled_at": reminder_data.get("scheduled_at").isoformat() if reminder_data.get("scheduled_at") else None,
                "sent_at": reminder_data.get("sent_at").isoformat() if reminder_data.get("sent_at") else None
            })
        
        return {"reminders": reminders, "count": len(reminders)}
        
    except Exception as e:
        logger.error(f"Error fetching reminder logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reminder logs"
        )

