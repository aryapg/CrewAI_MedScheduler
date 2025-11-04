"""
Reminder Agent - Handles appointment reminders via SMS/Email.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from backend.core.orchestrator import orchestrator
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)


def schedule_reminder(appointment_id: str, patient_name: str, doctor_name: str, 
                     appointment_date: str, appointment_time: str,
                     reminder_type: str = "sms", hours_before: int = 24) -> Dict[str, Any]:
    """
    Schedule a reminder for an appointment using the reminder agent.
    
    Args:
        appointment_id: ID of the appointment
        patient_name: Name of the patient
        doctor_name: Name of the doctor
        appointment_date: Date of the appointment
        appointment_time: Time of the appointment
        reminder_type: Type of reminder ('sms' or 'email')
        hours_before: Hours before appointment to send reminder
        
    Returns:
        Result from the reminder agent
    """
    task = f"Schedule a {reminder_type} reminder for appointment on {appointment_date} at {appointment_time}, {hours_before} hours before"
    
    context = {
        "action": "schedule_reminder",
        "appointment_id": appointment_id,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "reminder_type": reminder_type,
        "hours_before": hours_before
    }
    
    logger.info(f"Reminder Agent: Scheduling {reminder_type} reminder for appointment {appointment_id}")
    
    # Execute agent task
    result = orchestrator.execute_reminder_task(task, context)
    
    # Simulate sending reminder (mock)
    if settings.USE_MOCK_SMS or settings.USE_MOCK_EMAIL:
        logger.info(f"[MOCK {reminder_type.upper()}] Sending reminder to {patient_name}")
        logger.info(f"[MOCK] Message: Appointment reminder: {doctor_name} on {appointment_date} at {appointment_time}")
        logger.info(f"[MOCK] Scheduled for: {hours_before} hours before appointment")
    
    result["reminder_details"] = {
        "type": reminder_type,
        "hours_before": hours_before,
        "scheduled_at": datetime.utcnow().isoformat(),
        "mock": settings.USE_MOCK_SMS or settings.USE_MOCK_EMAIL
    }
    
    return result


def send_immediate_reminder(appointment_id: str, patient_name: str, 
                           doctor_name: str, appointment_date: str, 
                           appointment_time: str, reminder_type: str = "sms") -> Dict[str, Any]:
    """
    Send an immediate reminder for an appointment.
    
    Args:
        appointment_id: ID of the appointment
        patient_name: Name of the patient
        doctor_name: Name of the doctor
        appointment_date: Date of the appointment
        appointment_time: Time of the appointment
        reminder_type: Type of reminder ('sms' or 'email')
        
    Returns:
        Result from the reminder agent
    """
    task = f"Send immediate {reminder_type} reminder for appointment on {appointment_date} at {appointment_time}"
    
    context = {
        "action": "send_immediate",
        "appointment_id": appointment_id,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "reminder_type": reminder_type
    }
    
    logger.info(f"Reminder Agent: Sending immediate {reminder_type} reminder for appointment {appointment_id}")
    
    result = orchestrator.execute_reminder_task(task, context)
    
    # Simulate sending reminder (mock)
    if settings.USE_MOCK_SMS or settings.USE_MOCK_EMAIL:
        logger.info(f"[MOCK {reminder_type.upper()}] Sending immediate reminder to {patient_name}")
        logger.info(f"[MOCK] Message: Appointment reminder: {doctor_name} on {appointment_date} at {appointment_time}")
    
    result["reminder_details"] = {
        "type": reminder_type,
        "sent_at": datetime.utcnow().isoformat(),
        "immediate": True,
        "mock": settings.USE_MOCK_SMS or settings.USE_MOCK_EMAIL
    }
    
    return result

