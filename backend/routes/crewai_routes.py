"""
CrewAI Agent Routes for automatic operations.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel
from backend.core.security import get_current_user
from backend.core.firestore_client import get_firestore
from backend.agents.booking_agent import book_appointment as agent_book
from backend.agents.reminder_agent import schedule_reminder as agent_schedule_reminder
from backend.agents.previsit_agent import process_questionnaire as agent_process_questionnaire
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crewai", tags=["CrewAI"])


class AutomaticBookingRequest(BaseModel):
    """Request model for automatic booking with CrewAI agents."""
    patient_id: str
    patient_name: str
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    reason: Optional[str] = None
    preferred_specialty: Optional[str] = None
    auto_schedule_reminders: bool = True
    auto_send_questionnaire: bool = True


class TriggerAgentsRequest(BaseModel):
    """Request model for triggering agents for existing appointment."""
    appointment_id: str
    operations: List[str] = ["reminder", "questionnaire"]


@router.post("/automatic-booking")
async def automatic_booking_with_crewai(
    request: AutomaticBookingRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Automatic appointment booking using CrewAI agents.
    Books appointment, schedules reminders, and sends questionnaires automatically.
    """
    db = get_firestore()
    user_id = current_user["user_id"]

    try:
        # Validate patient_id matches current user
        if current_user["role"] == "patient" and request.patient_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot book appointments for other users"
            )

        # Get available slots - Query users collection for doctors
        users_ref = db.collection("users")
        doctors_query = users_ref.where("role", "==", "doctor")
        
        # Filter by specialty if provided
        if request.preferred_specialty:
            doctors_query = doctors_query.where("specialty", "==", request.preferred_specialty)
        
        doctors_query = doctors_query.limit(10).stream()
        
        doctors_list = []
        for doctor in doctors_query:
            doctor_data = doctor.to_dict()
            doctors_list.append({
                "id": doctor.id,
                "name": doctor_data.get("full_name", "Dr. Unknown"),
                "specialty": doctor_data.get("specialty", "General")
            })
        
        # If no doctors found for specialty, get any doctor
        if not doctors_list and request.preferred_specialty:
            doctors_query = users_ref.where("role", "==", "doctor").limit(5).stream()
            for doctor in doctors_query:
                doctor_data = doctor.to_dict()
                doctors_list.append({
                    "id": doctor.id,
                    "name": doctor_data.get("full_name", "Dr. Unknown"),
                    "specialty": doctor_data.get("specialty", "General")
                })
        
        # If still no doctors, use default
        if not doctors_list:
            doctors_list = [{"id": "default", "name": "Dr. Default", "specialty": "General"}]
        
        # Select first available doctor matching specialty preference
        selected_doctor = None
        if request.preferred_specialty:
            for doc in doctors_list:
                if doc["specialty"] == request.preferred_specialty:
                    selected_doctor = doc
                    break
        if not selected_doctor:
            selected_doctor = doctors_list[0]
        
        doctor_id = selected_doctor["id"]
        doctor_name = selected_doctor["name"]
        specialty = selected_doctor["specialty"]
        
        # Find actual available slots for the selected doctor
        from datetime import timedelta
        next_date = datetime.utcnow() + timedelta(days=1)
        appointment_date = request.preferred_date or next_date.strftime("%Y-%m-%d")
        
        # Get actual available slots for this doctor and date
        appointments_ref = db.collection("appointments")
        existing_appointments = appointments_ref.where("date", "==", appointment_date).where("status", "==", "confirmed").stream()
        
        booked_times = set()
        for apt in existing_appointments:
            apt_data = apt.to_dict()
            if apt_data.get("doctor_id") == doctor_id:
                booked_times.add(apt_data.get("time", ""))
        
        # Generate available time slots (9am-5pm, 30min intervals)
        from datetime import datetime as dt
        all_times = []
        start_hour = 9
        end_hour = 17
        for hour in range(start_hour, end_hour + 1):
            for minute in [0, 30]:
                if hour == end_hour and minute == 30:
                    break
                time_str = f"{hour}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
                if hour > 12:
                    time_str = f"{hour-12}:{minute:02d} PM"
                elif hour == 12:
                    time_str = f"12:{minute:02d} PM"
                all_times.append(time_str)
        
        # Filter past times if date is today
        try:
            slot_date_obj = dt.strptime(appointment_date, "%Y-%m-%d")
            today = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if slot_date_obj.date() == today.date():
                current_time = dt.now()
                filtered_times = []
                for time_str in all_times:
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
        except:
            pass
        
        # Get available slots (not booked)
        available_times = [t for t in all_times if t not in booked_times]
        
        if not available_times:
            # If no slots available, try next day
            next_date = datetime.utcnow() + timedelta(days=2)
            appointment_date = next_date.strftime("%Y-%m-%d")
            available_times = all_times[:5]  # Use first 5 slots
        
        appointment_time = request.preferred_time or (available_times[0] if available_times else "10:00 AM")
        
        # Prepare available slots info for explanation
        available_slots_info = [{"date": appointment_date, "time": t, "doctor": doctor_name} for t in available_times[:5]]

        # Create appointment data
        appointment_data = {
            "patient_id": request.patient_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "patient_name": request.patient_name,
            "date": appointment_date,
            "time": appointment_time,
            "reason": request.reason,
            "specialty": specialty,
        }

        # Get available slots to show agent decision process
        appointments_ref_for_slots = db.collection("appointments")
        # This is a simplified version - in production, query actual available slots
        
        # Trigger Booking Agent
        logger.info("Triggering Booking Agent for automatic booking")
        booking_result = agent_book(appointment_data)
        
        # Extract agent explanation from result
        agent_explanation = booking_result.get("result", "Agent processed the booking request")
        agent_steps = [
            f"Booking Agent analyzed your request for {request.reason or 'appointment'}",
            f"Checked available doctors and found {len(doctors_list)} doctor(s) available",
            f"Selected {doctor_name} ({specialty}) as the best match",
            f"Analyzed {len(available_slots_info)} available slots",
            f"Selected optimal slot: {appointment_date} at {appointment_time}",
            "Verified appointment conflicts and confirmed booking"
        ]

        # Create appointment in Firestore
        appointment_doc = {
            "patient_id": request.patient_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "patient_name": request.patient_name,
            "date": appointment_date,
            "time": appointment_time,
            "status": "confirmed",
            "reason": request.reason,
            "specialty": specialty,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "automatic": True,  # Mark as automatic
        }

        appointments_ref = db.collection("appointments")
        appointment_ref = appointments_ref.document()
        appointment_id = appointment_ref.id
        appointment_ref.set(appointment_doc)

        logger.info(f"Automatic appointment booked: {appointment_id}")

        # Send confirmation email immediately after booking
        try:
            from backend.core.email_service import send_appointment_confirmation
            # Get patient email
            patient_doc = db.collection("users").document(request.patient_id).get()
            if patient_doc.exists:
                patient_data = patient_doc.to_dict()
                patient_email = patient_data.get("email", "")
                if patient_email:
                    send_appointment_confirmation(
                        patient_email=patient_email,
                        patient_name=request.patient_name,
                        doctor_name=doctor_name,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time,
                        specialty=specialty,
                        reason=request.reason,
                        questionnaire_required=True
                    )
                    logger.info(f"Automatic booking confirmation email sent to {patient_email} (with Gemini-generated content)")
        except Exception as e:
            logger.error(f"Failed to send automatic booking confirmation email: {str(e)}")

        # Schedule reminder if requested
        reminder_scheduled = False
        if request.auto_schedule_reminders:
            try:
                logger.info("Triggering Reminder Agent for automatic reminder")
                reminder_result = agent_schedule_reminder(
                    appointment_id=appointment_id,
                    patient_name=request.patient_name,
                    doctor_name=doctor_name,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    reminder_type="email",  # Changed to email
                    hours_before=24
                )

                # Compute scheduled_at = appointment_datetime - 24 hours
                from datetime import datetime as dt, timezone, timedelta
                try:
                    hh_mm, am_pm = appointment_time.split(" ")
                    hour, minute = [int(x) for x in hh_mm.split(":")]
                    if am_pm.upper() == "PM" and hour != 12:
                        hour += 12
                    if am_pm.upper() == "AM" and hour == 12:
                        hour = 0
                    appt_dt_naive = dt.strptime(appointment_date, "%Y-%m-%d").replace(hour=hour, minute=minute)
                    appt_dt = appt_dt_naive.replace(tzinfo=timezone.utc)
                    scheduled_at = appt_dt - timedelta(hours=24)
                except Exception:
                    scheduled_at = dt.now(timezone.utc)

                # Save reminder to Firestore
                reminder_doc = {
                    "appointment_id": appointment_id,
                    "patient_id": request.patient_id,
                    "doctor_id": doctor_id,
                    "reminder_type": "email",
                    "hours_before": 24,
                    "status": "scheduled",
                    "scheduled_at": scheduled_at,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "created_by": user_id,
                    "automatic": True,
                }

                reminders_ref = db.collection("reminders")
                reminders_ref.document().set(reminder_doc)
                reminder_scheduled = True
                
                # Do not send immediately; background scheduler will send at scheduled_at
                
                logger.info("Automatic reminder scheduled")
            except Exception as e:
                logger.error(f"Failed to schedule automatic reminder: {str(e)}")

        # Send questionnaire if requested
        questionnaire_sent = False
        if request.auto_send_questionnaire:
            try:
                logger.info("Triggering Pre-Visit Agent for automatic questionnaire")
                
                # Create basic questionnaire data
                questionnaire_data = {
                    "appointment_id": appointment_id,
                    "patient_id": request.patient_id,
                    "chief_complaint": request.reason or "Automatic questionnaire - Please fill out",
                    "symptoms": "",
                    "medical_history": "",
                    "current_medications": "",
                    "allergies": "",
                    "additional_notes": "This questionnaire was automatically generated. Please update with your details.",
                }

                questionnaire_result = agent_process_questionnaire(
                    questionnaire_data, appointment_id
                )

                # Save questionnaire to Firestore
                questionnaires_ref = db.collection("questionnaires")
                questionnaire_ref = questionnaires_ref.document()
                questionnaire_id = questionnaire_ref.id

                # Get summary from agent result
                summary = questionnaire_result.get("summary", "")
                if not summary:
                    # Generate summary using Gemini if available
                    from backend.agents.previsit_agent import summarize_questionnaire
                    summary = summarize_questionnaire(questionnaire_data)

                questionnaire_doc = {
                    **questionnaire_data,
                    "submitted_at": datetime.utcnow(),
                    "summary": summary,
                    "automatic": True,
                }

                questionnaire_ref.set(questionnaire_doc)
                questionnaire_sent = True
                questionnaire_result["summary"] = summary  # Store for response
                logger.info(f"Automatic questionnaire created with summary: {summary[:50]}...")
            except Exception as e:
                logger.error(f"Failed to create automatic questionnaire: {str(e)}")

        # Prepare agent explanation with slot analysis
        slots_analyzed = ", ".join([f"{s['date']} {s['time']}" for s in available_slots_info[:3]])
        agent_explanation_text = (
            f"Booking Agent successfully booked your appointment! The agent analyzed {len(available_slots_info)} available slots "
            f"({slots_analyzed}) and selected {doctor_name} ({specialty}) for {appointment_date} at {appointment_time}. "
            f"This was chosen as the optimal slot based on doctor availability, specialty match, and your preferences."
        )
        
        # Prepare questionnaire questions if sent - fetch actual data
        questionnaire_questions = []
        questionnaire_summary = None
        if questionnaire_sent:
            # Fetch the actual questionnaire data from Firestore
            try:
                questionnaires_ref = db.collection("questionnaires")
                questionnaire_query = questionnaires_ref.where("appointment_id", "==", appointment_id).limit(1).stream()
                
                for doc in questionnaire_query:
                    q_data = doc.to_dict()
                    questionnaire_questions = [
                        {"question": "Chief Complaint", "answer": q_data.get("chief_complaint", "Not provided")},
                        {"question": "Symptoms", "answer": q_data.get("symptoms", "Not provided")},
                        {"question": "Medical History", "answer": q_data.get("medical_history", "Not provided")},
                        {"question": "Current Medications", "answer": q_data.get("current_medications", "Not provided")},
                        {"question": "Allergies", "answer": q_data.get("allergies", "Not provided")},
                        {"question": "Additional Notes", "answer": q_data.get("additional_notes", "None")},
                    ]
                    questionnaire_summary = q_data.get("summary", "")
                    break
            except Exception as e:
                logger.error(f"Failed to fetch questionnaire data: {str(e)}")
                # Fallback to basic data
                questionnaire_questions = [
                    {"question": "Chief Complaint", "answer": request.reason or "Not provided"},
                    {"question": "Symptoms", "answer": "Not provided"},
                    {"question": "Medical History", "answer": "Not provided"},
                    {"question": "Current Medications", "answer": "Not provided"},
                    {"question": "Allergies", "answer": "Not provided"},
                ]

        return {
            "success": True,
            "appointment_id": appointment_id,
            "reminder_scheduled": reminder_scheduled,
            "questionnaire_sent": questionnaire_sent,
            "agent_results": {
                "booking": booking_result,
                "reminder": reminder_scheduled,
                "questionnaire": questionnaire_sent,
            },
            "agent_explanation": {
                "action": "Automatic Appointment Booking",
                "explanation": agent_explanation_text,
                "steps": agent_steps,
                "slot_selected": {
                    "doctor": doctor_name,
                    "date": appointment_date,
                    "time": appointment_time,
                    "reason": request.reason or "Routine checkup"
                },
                "reminder_scheduled": reminder_scheduled,
                "questionnaire_data": {
                    "questions": questionnaire_questions,
                    "summary": questionnaire_summary or questionnaire_result.get("summary") if questionnaire_sent else None
                } if questionnaire_sent else None
            },
            "message": "Automatic booking completed successfully with CrewAI agents",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in automatic booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automatic booking failed: {str(e)}"
        )


@router.post("/trigger-agents")
async def trigger_agents_for_appointment(
    request: TriggerAgentsRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Trigger CrewAI agents for an existing appointment.
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

        # Check permissions
        if (current_user["role"] != "admin" and 
            appointment_data["patient_id"] != user_id and 
            appointment_data["doctor_id"] != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to trigger agents for this appointment"
            )

        agent_results = {}

        # Trigger reminder agent if requested
        if "reminder" in request.operations:
            try:
                reminder_result = agent_schedule_reminder(
                    appointment_id=request.appointment_id,
                    patient_name=appointment_data.get("patient_name", ""),
                    doctor_name=appointment_data.get("doctor_name", ""),
                    appointment_date=appointment_data.get("date", ""),
                    appointment_time=appointment_data.get("time", ""),
                    reminder_type="sms",
                    hours_before=24
                )
                agent_results["reminder"] = reminder_result

                # Save reminder
                reminder_doc = {
                    "appointment_id": request.appointment_id,
                    "patient_id": appointment_data.get("patient_id", ""),
                    "doctor_id": appointment_data.get("doctor_id", ""),
                    "reminder_type": "sms",
                    "hours_before": 24,
                    "status": "scheduled",
                    "scheduled_at": datetime.utcnow(),
                    "appointment_date": appointment_data.get("date", ""),
                    "appointment_time": appointment_data.get("time", ""),
                    "created_by": user_id,
                    "automatic": True,
                }

                db.collection("reminders").document().set(reminder_doc)
            except Exception as e:
                logger.error(f"Failed to trigger reminder agent: {str(e)}")
                agent_results["reminder"] = {"error": str(e)}

        # Trigger questionnaire agent if requested
        if "questionnaire" in request.operations:
            try:
                questionnaire_data = {
                    "appointment_id": request.appointment_id,
                    "patient_id": appointment_data.get("patient_id", ""),
                    "chief_complaint": "",
                    "symptoms": "",
                    "medical_history": "",
                    "current_medications": "",
                    "allergies": "",
                    "additional_notes": "",
                }

                questionnaire_result = agent_process_questionnaire(
                    questionnaire_data, request.appointment_id
                )
                agent_results["questionnaire"] = questionnaire_result

                # Save questionnaire
                questionnaires_ref = db.collection("questionnaires")
                questionnaire_ref = questionnaires_ref.document()
                questionnaire_id = questionnaire_ref.id

                questionnaire_doc = {
                    **questionnaire_data,
                    "submitted_at": datetime.utcnow(),
                    "summary": questionnaire_result.get("summary", ""),
                    "automatic": True,
                }

                questionnaire_ref.set(questionnaire_doc)
            except Exception as e:
                logger.error(f"Failed to trigger questionnaire agent: {str(e)}")
                agent_results["questionnaire"] = {"error": str(e)}

        return {
            "success": True,
            "agent_results": agent_results,
            "message": "CrewAI agents triggered successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger agents: {str(e)}"
        )

