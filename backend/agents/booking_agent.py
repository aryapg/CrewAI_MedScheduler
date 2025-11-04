"""
Booking Agent - Handles appointment booking, rescheduling, and cancellation.
"""

from typing import Dict, Any
from backend.core.orchestrator import orchestrator
import logging

logger = logging.getLogger(__name__)


def book_appointment(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Book a new appointment using the booking agent.
    
    Args:
        appointment_data: Dictionary containing appointment details
        
    Returns:
        Result from the booking agent
    """
    task = f"Book an appointment for {appointment_data.get('patient_name', 'patient')} with {appointment_data.get('doctor_name', 'doctor')} on {appointment_data.get('date', 'date')} at {appointment_data.get('time', 'time')}"
    
    context = {
        "action": "book",
        "appointment_data": appointment_data
    }
    
    logger.info(f"Booking Agent: Executing booking task for appointment")
    result = orchestrator.execute_booking_task(task, context)
    
    return result


def reschedule_appointment(appointment_id: str, new_date: str, new_time: str, reason: str = "") -> Dict[str, Any]:
    """
    Reschedule an existing appointment using the booking agent.
    
    Args:
        appointment_id: ID of the appointment to reschedule
        new_date: New appointment date
        new_time: New appointment time
        reason: Optional reason for rescheduling
        
    Returns:
        Result from the booking agent
    """
    task = f"Reschedule appointment {appointment_id} to {new_date} at {new_time}"
    if reason:
        task += f". Reason: {reason}"
    
    context = {
        "action": "reschedule",
        "appointment_id": appointment_id,
        "new_date": new_date,
        "new_time": new_time,
        "reason": reason
    }
    
    logger.info(f"Booking Agent: Executing reschedule task for appointment {appointment_id}")
    result = orchestrator.execute_booking_task(task, context)
    
    return result


def cancel_appointment(appointment_id: str, reason: str = "") -> Dict[str, Any]:
    """
    Cancel an appointment using the booking agent.
    
    Args:
        appointment_id: ID of the appointment to cancel
        reason: Optional reason for cancellation
        
    Returns:
        Result from the booking agent
    """
    task = f"Cancel appointment {appointment_id}"
    if reason:
        task += f". Reason: {reason}"
    
    context = {
        "action": "cancel",
        "appointment_id": appointment_id,
        "reason": reason
    }
    
    logger.info(f"Booking Agent: Executing cancellation task for appointment {appointment_id}")
    result = orchestrator.execute_booking_task(task, context)
    
    return result

