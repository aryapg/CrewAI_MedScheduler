"""
Main FastAPI application entry point.
Medical Appointment Scheduler Backend with CrewAI, Firestore, and JWT Authentication.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
import os

# Add parent directory to path so we can import backend modules
# This must be done BEFORE importing backend modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Check Python version
if sys.version_info < (3, 7):
    print("ERROR: Python 3.7+ required. Current version:", sys.version)
    sys.exit(1)

try:
    from contextlib import asynccontextmanager
except ImportError:
    print("ERROR: asynccontextmanager requires Python 3.7+")
    sys.exit(1)

from backend.core.config import settings
from backend.core.firestore_client import initialize_firebase, get_firestore
from datetime import datetime, timezone
import asyncio
from backend.routes import auth, appointments, reminders, questionnaire, analytics, crewai_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def _reminder_sender_loop():
    """Background loop to send due reminders.
    Checks Firestore every 60 seconds for reminders with status 'scheduled'
    and scheduled_at <= now, then sends email and marks them as 'sent'.
    """
    db = get_firestore()
    while True:
        try:
            now_iso = datetime.now(timezone.utc)
            reminders_ref = db.collection("reminders")
            # Fetch scheduled reminders; Firestore cannot filter by time <= now with two inequalities easily,
            # so fetch a small window and filter in app.
            query = reminders_ref.where("status", "==", "scheduled").limit(50).stream()
            for doc in query:
                data = doc.to_dict()
                scheduled_at = data.get("scheduled_at")
                if not scheduled_at:
                    continue
                # Firestore returns datetime with tz; ensure comparable
                try:
                    if scheduled_at <= now_iso:
                        # Fetch patient email
                        patient_id = data.get("patient_id", "")
                        appointment_date = data.get("appointment_date", "")
                        appointment_time = data.get("appointment_time", "")
                        doctor_id = data.get("doctor_id", "")
                        # Look up patient & doctor
                        patient_email = ""
                        patient_name = "Patient"
                        doctor_name = "Doctor"
                        specialty = data.get("specialty", "General")
                        try:
                            patient_doc = db.collection("users").document(patient_id).get()
                            if patient_doc.exists:
                                p = patient_doc.to_dict()
                                patient_email = p.get("email", "")
                                patient_name = p.get("full_name", patient_name)
                        except Exception:
                            pass
                        try:
                            if doctor_id:
                                doctor_doc = db.collection("users").document(doctor_id).get()
                                if doctor_doc.exists:
                                    d = doctor_doc.to_dict()
                                    doctor_name = d.get("full_name", doctor_name)
                                    specialty = d.get("specialty", specialty)
                        except Exception:
                            pass
                        if patient_email:
                            from backend.core.email_service import send_appointment_reminder
                            send_appointment_reminder(
                                patient_email=patient_email,
                                patient_name=patient_name,
                                doctor_name=doctor_name,
                                appointment_date=appointment_date,
                                appointment_time=appointment_time,
                                specialty=specialty,
                                reason=data.get("reason")
                            )
                            # Mark sent
                            doc.reference.update({
                                "status": "sent",
                                "sent_at": datetime.now(timezone.utc)
                            })
                            logger.info(f"Reminder sent to {patient_email} for {appointment_date} {appointment_time}")
                except Exception as send_err:
                    logger.warning(f"Reminder send check failed for {doc.id}: {send_err}")
        except Exception as e:
            logger.warning(f"Reminder sender loop error: {e}")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Medical Scheduler Backend...")
    try:
        # Initialize Firebase
        db = initialize_firebase()
        logger.info(f"Firebase initialized successfully. Project ID: {settings.FIREBASE_PROJECT_ID}")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        logger.warning("Backend will continue, but Firestore operations may fail.")
    
    # Start background reminder loop
    reminder_task = None
    try:
        reminder_task = asyncio.create_task(_reminder_sender_loop())
    except Exception as e:
        logger.warning(f"Failed to start reminder loop: {e}")

    yield
    
    # Shutdown
    logger.info("Shutting down Medical Scheduler Backend...")
    # Cancel background task
    try:
        if reminder_task:
            reminder_task.cancel()
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title="Medical Appointment Scheduler API",
    description="Backend API for Medical Appointment Scheduler using CrewAI, Firestore, and JWT Authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(reminders.router)
app.include_router(questionnaire.router)
app.include_router(analytics.router)
app.include_router(crewai_routes.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Medical Appointment Scheduler API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "firebase_initialized": True,  # Can be enhanced to check actual connection
        "mock_ai": settings.USE_MOCK_AI
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8000))  # use Render’s PORT if available
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # bind to all interfaces (required by Render)
        port=port,
        log_level="info"
    )

