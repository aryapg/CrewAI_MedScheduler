"""
Appointment routes for booking, rescheduling, and cancellation.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Optional
from datetime import datetime
from backend.models.appointment_model import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, 
    AppointmentStatus, AvailableSlot
)
from backend.core.security import get_current_user
from backend.core.firestore_client import get_firestore
from backend.agents.booking_agent import (
    book_appointment as agent_book,
    reschedule_appointment as agent_reschedule,
    cancel_appointment as agent_cancel
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Appointments"])


def _appointment_doc_to_response(doc_id: str, doc_data: dict) -> AppointmentResponse:
    """Convert Firestore document to AppointmentResponse."""
    return AppointmentResponse(
        id=doc_id,
        patient_id=doc_data.get("patient_id", ""),
        doctor_id=doc_data.get("doctor_id", ""),
        doctor_name=doc_data.get("doctor_name", ""),
        patient_name=doc_data.get("patient_name", ""),
        date=doc_data.get("date", ""),
        time=doc_data.get("time", ""),
        status=AppointmentStatus(doc_data.get("status", "pending")),
        reason=doc_data.get("reason"),
        specialty=doc_data.get("specialty"),
        created_at=doc_data.get("created_at"),
        updated_at=doc_data.get("updated_at")
    )


@router.get("/slots", response_model=List[AvailableSlot])
async def get_available_slots(
    doctor_id: Optional[str] = None,
    date: Optional[str] = None,
    specialty: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get available appointment slots with continuous time slots (9am, 9:30am, 10am, etc.).
    Checks existing appointments to show which slots are booked/available.
    """
    db = get_firestore()
    
    try:
        # Get available doctors
        doctors_ref = db.collection("users").where("role", "==", "doctor")
        
        if doctor_id:
            doctors_ref = doctors_ref.where("__name__", "==", doctor_id)
        if specialty:
            doctors_ref = doctors_ref.where("specialty", "==", specialty)
        
        # Stream doctors; if specialty filter yields none, fallback to all doctors
        doctors_cursor = list(doctors_ref.stream())
        if not doctors_cursor and specialty:
            try:
                fallback_ref = db.collection("users").where("role", "==", "doctor")
                doctors_cursor = list(fallback_ref.stream())
                logger.info(f"No doctors found for specialty '{specialty}', falling back to all doctors")
            except Exception:
                doctors_cursor = []
        
        # Generate continuous time slots: 9:00 AM to 5:00 PM, 30-minute intervals
        from datetime import datetime, timedelta
        base_date = date or datetime.utcnow().strftime("%Y-%m-%d")
        
        # Parse base date for slot generation
        try:
            slot_date = datetime.strptime(base_date, "%Y-%m-%d")
        except:
            slot_date = datetime.utcnow()
        
        # Generate all possible time slots (9:00 AM to 5:00 PM)
        all_times = []
        start_hour = 9
        end_hour = 17
        for hour in range(start_hour, end_hour + 1):
            for minute in [0, 30]:
                if hour == end_hour and minute == 30:  # Skip 5:30 PM
                    break
                time_str = f"{hour}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
                if hour > 12:
                    time_str = f"{hour-12}:{minute:02d} PM"
                elif hour == 12:
                    time_str = f"12:{minute:02d} PM"
                all_times.append(time_str)
        
        # Filter out past times if date is today
        from datetime import datetime as dt
        try:
            slot_date_obj = dt.strptime(base_date, "%Y-%m-%d")
            today = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if slot_date_obj.date() == today.date():
                # Filter out times that have already passed today
                current_time = dt.now()
                filtered_times = []
                for time_str in all_times:
                    # Parse time string to compare
                    hour_str = time_str.split(":")[0]
                    minute_str = time_str.split(":")[1].split(" ")[0]
                    am_pm = time_str.split(" ")[1]
                    
                    hour = int(hour_str)
                    minute = int(minute_str)
                    if am_pm == "PM" and hour != 12:
                        hour += 12
                    elif am_pm == "AM" and hour == 12:
                        hour = 0
                    
                    slot_time = today.replace(hour=hour, minute=minute)
                    if slot_time > current_time:
                        filtered_times.append(time_str)
                
                all_times = filtered_times
                # If no times remain today, fallback to next day full schedule
                if not all_times:
                    from datetime import timedelta as _td
                    next_day = slot_date + _td(days=1)
                    base_date = next_day.strftime("%Y-%m-%d")
                    all_times = []
                    for hour in range(start_hour, end_hour + 1):
                        for minute in [0, 30]:
                            if hour == end_hour and minute == 30:
                                break
                            ts = f"{hour}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
                            if hour > 12:
                                ts = f"{hour-12}:{minute:02d} PM"
                            elif hour == 12:
                                ts = f"12:{minute:02d} PM"
                            all_times.append(ts)
        except Exception as e:
            logger.warning(f"Error filtering past times: {str(e)}")
            # Keep all times if filtering fails
        
        slots = []
        
        # Get existing appointments for the date to check availability
        appointments_ref = db.collection("appointments")
        existing_appointments = appointments_ref.where("date", "==", base_date).where("status", "==", "confirmed").stream()
        
        booked_slots = {}  # {(doctor_id, time): True}
        for apt in existing_appointments:
            apt_data = apt.to_dict()
            apt_doctor_id = apt_data.get("doctor_id", "")
            apt_time = apt_data.get("time", "")
            if apt_doctor_id and apt_time:
                booked_slots[(apt_doctor_id, apt_time)] = True
        
        # Create slots for each doctor
        for doctor in doctors_cursor:
            doctor_data = doctor.to_dict()
            doctor_id_val = doctor.id
            
            # Add all time slots for this doctor
            for time in all_times:
                is_booked = booked_slots.get((doctor_id_val, time), False)
                
                # Add all slots (both booked and available) with availability flag
                slots.append(AvailableSlot(
                    date=base_date,
                    time=time,
                    doctor_name=doctor_data.get("full_name", "Dr. Unknown"),
                    doctor_id=doctor_id_val,
                    specialty=doctor_data.get("specialty"),
                    is_available=not is_booked
                ))
        
        # If no doctors found, return default slots
        if not slots:
            # Generate default slots for demo
            default_times = all_times[:10]  # First 10 slots
            for time in default_times:
                slots.append(AvailableSlot(
                    date=base_date,
                    time=time,
                    doctor_name="Dr. Sarah Smith",
                    doctor_id="default",
                    specialty="Cardiologist"
                ))
        
        return slots
        
    except Exception as e:
        logger.error(f"Error fetching slots: {str(e)}")
        # Return default slots on error
        default_times = ["9:00 AM", "9:30 AM", "10:00 AM", "10:30 AM", "11:00 AM"]
        return [
            AvailableSlot(
                date=date or datetime.utcnow().strftime("%Y-%m-%d"),
                time=time,
                doctor_name="Dr. Sarah Smith",
                doctor_id="default",
                specialty="Cardiologist"
            ) for time in default_times
        ]


@router.post("/book", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment: AppointmentCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Book a new appointment.
    Triggers booking agent and stores appointment in Firestore.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    
    try:
        # Validate that patient_id matches current user (for patients)
        if current_user["role"] == "patient" and appointment.patient_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot book appointments for other users"
            )
        
        # Trigger booking agent
        agent_result = agent_book(appointment.dict())
        logger.info(f"Booking agent result: {agent_result}")
        
        # Create appointment document
        appointment_doc = {
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "doctor_name": appointment.doctor_name,
            "patient_name": appointment.patient_name,
            "date": appointment.date,
            "time": appointment.time,
            "status": "confirmed",
            "reason": appointment.reason,
            "specialty": appointment.specialty,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Add to Firestore
        appointments_ref = db.collection("appointments")
        appointment_ref = appointments_ref.document()
        appointment_id = appointment_ref.id
        appointment_ref.set(appointment_doc)
        
        logger.info(f"Appointment booked: {appointment_id}")
        
        # Send confirmation email with Gemini-generated content
        try:
            from backend.core.email_service import send_appointment_confirmation
            # Get patient email
            patient_doc = db.collection("users").document(appointment.patient_id).get()
            if patient_doc.exists:
                patient_data = patient_doc.to_dict()
                patient_email = patient_data.get("email", "")
                if patient_email:
                    send_appointment_confirmation(
                        patient_email=patient_email,
                        patient_name=appointment.patient_name,
                        doctor_name=appointment.doctor_name,
                        appointment_date=appointment.date,
                        appointment_time=appointment.time,
                        specialty=appointment.specialty or "General",
                        reason=appointment.reason,
                        questionnaire_required=True  # Always require questionnaire
                    )
                    logger.info(f"Confirmation email sent to {patient_email} (with Gemini-generated content)")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {str(e)}")
        
        # Return appointment response
        appointment_data = appointment_ref.get().to_dict()
        return _appointment_doc_to_response(appointment_id, appointment_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to book appointment: {str(e)}"
        )


@router.put("/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_time: str,
    reason: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Reschedule an existing appointment.
    Triggers booking agent and updates appointment in Firestore.
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
        if (current_user["role"] != "admin" and 
            appointment_data["patient_id"] != user_id and 
            appointment_data["doctor_id"] != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to reschedule this appointment"
            )
        
        # Trigger booking agent
        agent_result = agent_reschedule(appointment_id, new_date, new_time, reason or "")
        logger.info(f"Reschedule agent result: {agent_result}")
        
        # Update appointment
        appointment_ref.update({
            "date": new_date,
            "time": new_time,
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"Appointment rescheduled: {appointment_id}")
        
        # Return updated appointment
        updated_data = appointment_ref.get().to_dict()
        return _appointment_doc_to_response(appointment_id, updated_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule appointment: {str(e)}"
        )


@router.delete("/cancel", status_code=status.HTTP_200_OK)
async def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cancel an appointment.
    Triggers booking agent and updates appointment status in Firestore.
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
        if (current_user["role"] != "admin" and 
            appointment_data["patient_id"] != user_id and 
            appointment_data["doctor_id"] != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this appointment"
            )
        
        # Trigger booking agent
        agent_result = agent_cancel(appointment_id, reason or "")
        logger.info(f"Cancel agent result: {agent_result}")
        
        # Update appointment status
        appointment_ref.update({
            "status": "cancelled",
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"Appointment cancelled: {appointment_id}")
        
        return {"message": "Appointment cancelled successfully", "appointment_id": appointment_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel appointment: {str(e)}"
        )


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    role: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get appointments for the current user.
    Patients see their appointments, doctors see their appointments.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        appointments_ref = db.collection("appointments")
        
        # Filter by role
        if user_role == "patient":
            query = appointments_ref.where("patient_id", "==", user_id)
        elif user_role == "doctor":
            query = appointments_ref.where("doctor_id", "==", user_id)
        elif user_role == "admin":
            query = appointments_ref  # Admins see all
        else:
            query = appointments_ref.where("patient_id", "==", user_id)
        
        appointments = []
        for doc in query.stream():
            appointments.append(_appointment_doc_to_response(doc.id, doc.to_dict()))
        
        return appointments
        
    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch appointments"
        )

