"""
Seed script to add predefined doctors to Firestore.
Run this once to populate the database with doctors.
"""

import sys
import os

# Add project root to path (parent of backend directory)
current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/scripts
backend_dir = os.path.dirname(current_dir)  # backend
project_root = os.path.dirname(backend_dir)  # project root
sys.path.insert(0, project_root)

from backend.core.firestore_client import get_firestore, initialize_firebase
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Predefined doctors with different specialties - AT LEAST 2 per specialty
DOCTORS = [
    # Cardiologists (2)
    {
        "email": "dr.smith.cardio@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Sarah Smith",
        "role": "doctor",
        "specialty": "Cardiologist",
        "phone": "+1-555-0101",
        "bio": "Experienced cardiologist with 15 years of practice. Specializes in heart disease prevention and treatment."
    },
    {
        "email": "dr.anderson.cardio@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. John Anderson",
        "role": "doctor",
        "specialty": "Cardiologist",
        "phone": "+1-555-0109",
        "bio": "Cardiologist specializing in interventional cardiology and heart rhythm disorders."
    },
    # General Physicians (2)
    {
        "email": "dr.johnson.general@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Michael Johnson",
        "role": "doctor",
        "specialty": "General Physician",
        "phone": "+1-555-0102",
        "bio": "General physician providing comprehensive primary care services."
    },
    {
        "email": "dr.taylor.general@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Jennifer Taylor",
        "role": "doctor",
        "specialty": "General Physician",
        "phone": "+1-555-0110",
        "bio": "Family medicine physician with expertise in preventive care and chronic disease management."
    },
    # Neurologists (2)
    {
        "email": "dr.williams.neuro@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Emily Williams",
        "role": "doctor",
        "specialty": "Neurologist",
        "phone": "+1-555-0103",
        "bio": "Neurologist specializing in brain and nervous system disorders."
    },
    {
        "email": "dr.martinez.neuro@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Carlos Martinez",
        "role": "doctor",
        "specialty": "Neurologist",
        "phone": "+1-555-0111",
        "bio": "Neurologist with expertise in stroke, epilepsy, and movement disorders."
    },
    # Orthopedic Surgeons (2)
    {
        "email": "dr.brown.ortho@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. James Brown",
        "role": "doctor",
        "specialty": "Orthopedic Surgeon",
        "phone": "+1-555-0104",
        "bio": "Orthopedic surgeon with expertise in bone and joint treatments."
    },
    {
        "email": "dr.thomas.ortho@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Christopher Thomas",
        "role": "doctor",
        "specialty": "Orthopedic Surgeon",
        "phone": "+1-555-0112",
        "bio": "Orthopedic surgeon specializing in sports medicine and joint replacement surgery."
    },
    # Dermatologists (2)
    {
        "email": "dr.davis.dermat@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Patricia Davis",
        "role": "doctor",
        "specialty": "Dermatologist",
        "phone": "+1-555-0105",
        "bio": "Dermatologist specializing in skin, hair, and nail conditions."
    },
    {
        "email": "dr.garcia.dermat@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Maria Garcia",
        "role": "doctor",
        "specialty": "Dermatologist",
        "phone": "+1-555-0113",
        "bio": "Dermatologist with expertise in cosmetic dermatology and skin cancer treatment."
    },
    # Pediatricians (2)
    {
        "email": "dr.miller.pedia@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Robert Miller",
        "role": "doctor",
        "specialty": "Pediatrician",
        "phone": "+1-555-0106",
        "bio": "Pediatrician providing specialized care for children and adolescents."
    },
    {
        "email": "dr.jackson.pedia@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Amanda Jackson",
        "role": "doctor",
        "specialty": "Pediatrician",
        "phone": "+1-555-0114",
        "bio": "Pediatrician specializing in developmental pediatrics and childhood immunizations."
    },
    # Psychiatrists (2)
    {
        "email": "dr.wilson.psych@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Lisa Wilson",
        "role": "doctor",
        "specialty": "Psychiatrist",
        "phone": "+1-555-0107",
        "bio": "Psychiatrist specializing in mental health and behavioral disorders."
    },
    {
        "email": "dr.rodriguez.psych@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Daniel Rodriguez",
        "role": "doctor",
        "specialty": "Psychiatrist",
        "phone": "+1-555-0115",
        "bio": "Psychiatrist with expertise in anxiety disorders, depression, and cognitive behavioral therapy."
    },
    # Oncologists (2)
    {
        "email": "dr.moore.onco@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. David Moore",
        "role": "doctor",
        "specialty": "Oncologist",
        "phone": "+1-555-0108",
        "bio": "Oncologist specializing in cancer diagnosis and treatment."
    },
    {
        "email": "dr.lee.onco@medscheduler.com",
        "password": "Doctor@123",
        "full_name": "Dr. Susan Lee",
        "role": "doctor",
        "specialty": "Oncologist",
        "phone": "+1-555-0116",
        "bio": "Medical oncologist specializing in breast cancer and hematologic malignancies."
    }
]


def seed_doctors():
    """Add predefined doctors to Firestore."""
    # Initialize Firebase first
    initialize_firebase()
    db = get_firestore()
    users_ref = db.collection("users")
    
    created_count = 0
    skipped_count = 0
    
    for doctor_data in DOCTORS:
        try:
            # Check if doctor already exists by email
            existing = users_ref.where("email", "==", doctor_data["email"]).limit(1).stream()
            if any(existing):
                logger.info(f"Doctor {doctor_data['full_name']} already exists, skipping...")
                skipped_count += 1
                continue
            
            # Hash password using bcrypt
            from backend.core.security import get_password_hash
            hashed_password = get_password_hash(doctor_data["password"])
            
            # Create doctor user
            doctor_user = {
                "email": doctor_data["email"],
                "password_hash": hashed_password,
                "full_name": doctor_data["full_name"],
                "role": doctor_data["role"],
                "phone": doctor_data["phone"],
                "specialty": doctor_data["specialty"],
                "bio": doctor_data["bio"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            users_ref.document().set(doctor_user)
            logger.info(f"Created doctor: {doctor_data['full_name']} ({doctor_data['specialty']})")
            created_count += 1
            
        except Exception as e:
            logger.error(f"Error creating doctor {doctor_data['full_name']}: {str(e)}")
    
    logger.info(f"\n✅ Seeding complete!")
    logger.info(f"   Created: {created_count} doctors")
    logger.info(f"   Skipped: {skipped_count} doctors (already exist)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_doctors()

