"""
Questionnaire routes for pre-visit questionnaires.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Optional
from datetime import datetime
from backend.models.questionnaire_model import (
    QuestionnaireSubmit, QuestionnaireResponse
)
from backend.core.security import get_current_user
from backend.core.firestore_client import get_firestore
from backend.agents.previsit_agent import process_questionnaire as agent_process
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/questionnaire", tags=["Questionnaires"])


def _questionnaire_doc_to_response(doc_id: str, doc_data: dict) -> QuestionnaireResponse:
    """Convert Firestore document to QuestionnaireResponse."""
    return QuestionnaireResponse(
        id=doc_id,
        appointment_id=doc_data.get("appointment_id", ""),
        patient_id=doc_data.get("patient_id", ""),
        chief_complaint=doc_data.get("chief_complaint"),
        symptoms=doc_data.get("symptoms"),
        medical_history=doc_data.get("medical_history"),
        current_medications=doc_data.get("current_medications"),
        allergies=doc_data.get("allergies"),
        additional_notes=doc_data.get("additional_notes"),
        summary=doc_data.get("summary"),
        submitted_at=doc_data.get("submitted_at")
    )


@router.get("/{appointment_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    appointment_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get questionnaire for a specific appointment.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        # Check appointment exists and user has access
        appointment_ref = db.collection("appointments").document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        appointment_data = appointment_doc.to_dict()
        
        # Check permissions
        if (user_role == "patient" and appointment_data["patient_id"] != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this questionnaire"
            )
        
        # Get questionnaire
        questionnaires_ref = db.collection("questionnaires")
        questionnaire_query = questionnaires_ref.where("appointment_id", "==", appointment_id).limit(1).stream()
        
        questionnaire_doc = None
        questionnaire_id = None
        
        for doc in questionnaire_query:
            questionnaire_doc = doc.to_dict()
            questionnaire_id = doc.id
            break
        
        if not questionnaire_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questionnaire not found for this appointment"
            )
        
        return _questionnaire_doc_to_response(questionnaire_id, questionnaire_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching questionnaire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch questionnaire"
        )


@router.post("/submit", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def submit_questionnaire(
    questionnaire: QuestionnaireSubmit,
    current_user: Dict = Depends(get_current_user)
):
    """
    Submit a pre-visit questionnaire.
    Triggers pre-visit agent for processing and summarization.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        # Check appointment exists and user has access
        appointment_ref = db.collection("appointments").document(questionnaire.appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        appointment_data = appointment_doc.to_dict()
        
        # Check permissions (only patients can submit questionnaires for their appointments)
        if user_role != "patient" or appointment_data["patient_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only patients can submit questionnaires for their appointments"
            )
        
        # Check if questionnaire already exists
        questionnaires_ref = db.collection("questionnaires")
        existing_query = questionnaires_ref.where("appointment_id", "==", questionnaire.appointment_id).limit(1).stream()
        
        questionnaire_id = None
        for doc in existing_query:
            questionnaire_id = doc.id
            break
        
        # Prepare questionnaire data
        questionnaire_dict = questionnaire.dict()
        questionnaire_dict["patient_id"] = user_id
        questionnaire_dict["submitted_at"] = datetime.utcnow()
        
        # Trigger pre-visit agent for processing
        agent_result = agent_process(questionnaire_dict, questionnaire.appointment_id)
        logger.info(f"Pre-visit agent result: {agent_result}")
        
        # Add summary from agent result
        if agent_result.get("summary"):
            questionnaire_dict["summary"] = agent_result["summary"]
        
        # Save to Firestore
        if questionnaire_id:
            # Update existing questionnaire
            questionnaires_ref.document(questionnaire_id).update(questionnaire_dict)
            logger.info(f"Questionnaire updated: {questionnaire_id}")
        else:
            # Create new questionnaire
            questionnaire_ref = questionnaires_ref.document()
            questionnaire_id = questionnaire_ref.id
            questionnaire_ref.set(questionnaire_dict)
            logger.info(f"Questionnaire created: {questionnaire_id}")
        
        # Return questionnaire response
        saved_doc = questionnaires_ref.document(questionnaire_id).get()
        return _questionnaire_doc_to_response(questionnaire_id, saved_doc.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting questionnaire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit questionnaire: {str(e)}"
        )


@router.get("/appointment/{appointment_id}/summary")
async def get_questionnaire_summary(
    appointment_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get AI-generated summary of a questionnaire.
    """
    db = get_firestore()
    user_id = current_user["user_id"]
    user_role = current_user["role"]
    
    try:
        # Check appointment exists
        appointment_ref = db.collection("appointments").document(appointment_id)
        appointment_doc = appointment_ref.get()
        
        if not appointment_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        appointment_data = appointment_doc.to_dict()
        
        # Check permissions (doctors and admins can view summaries)
        if (user_role == "patient" and appointment_data["patient_id"] != user_id):
            if user_role not in ["doctor", "admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this summary"
                )
        
        # Get questionnaire
        questionnaires_ref = db.collection("questionnaires")
        questionnaire_query = questionnaires_ref.where("appointment_id", "==", appointment_id).limit(1).stream()
        
        questionnaire_doc = None
        for doc in questionnaire_query:
            questionnaire_doc = doc.to_dict()
            break
        
        if not questionnaire_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questionnaire not found for this appointment"
            )
        
        summary = questionnaire_doc.get("summary")
        
        if not summary:
            # Generate summary on the fly
            agent_result = agent_process(questionnaire_doc, appointment_id)
            summary = agent_result.get("summary", "No summary available")
            
            # Save the generated summary
            doc_ref = questionnaires_ref.where("appointment_id", "==", appointment_id).limit(1).stream()
            for doc in doc_ref:
                doc.reference.update({"summary": summary})
                break
        
        return {
            "appointment_id": appointment_id,
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching questionnaire summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch questionnaire summary"
        )

