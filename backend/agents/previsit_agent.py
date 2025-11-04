"""
Pre-Visit Agent - Handles questionnaire collection and summarization.
"""

from typing import Dict, Any, Optional
from backend.core.orchestrator import orchestrator
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Gemini integration for summarization
gemini_model = None

if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use FREE Gemini model (not pro)
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Gemini API initialized successfully")
    except ImportError:
        logger.warning("google-generativeai not installed. Gemini summarization will be disabled.")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini: {e}")


def summarize_questionnaire(questionnaire_data: Dict[str, Any]) -> str:
    """
    Summarize questionnaire data using Gemini API if available.
    
    Args:
        questionnaire_data: Dictionary containing questionnaire responses
        
    Returns:
        Summary string
    """
    if gemini_model is None:
        # Fallback to simple summary if Gemini is not available
        return _create_simple_summary(questionnaire_data)
    
    try:
        prompt = f"""
        Summarize the following pre-visit medical questionnaire in a concise, professional format:
        
        {questionnaire_data}
        
        Provide a clear summary highlighting:
        1. Chief complaint/primary concern
        2. Current symptoms
        3. Medical history (relevant)
        4. Current medications
        5. Any urgent concerns
        
        Keep the summary under 300 words.
        """
        
        response = gemini_model.generate_content(prompt)
        summary = response.text
        logger.info("Questionnaire summarized using Gemini API")
        return summary
    except Exception as e:
        logger.error(f"Error using Gemini API: {e}, falling back to simple summary")
        return _create_simple_summary(questionnaire_data)


def _create_simple_summary(questionnaire_data: Dict[str, Any]) -> str:
    """Create a simple summary without AI."""
    summary_parts = []
    
    if questionnaire_data.get("chief_complaint"):
        summary_parts.append(f"Chief Complaint: {questionnaire_data['chief_complaint']}")
    
    if questionnaire_data.get("symptoms"):
        summary_parts.append(f"Symptoms: {questionnaire_data['symptoms']}")
    
    if questionnaire_data.get("medical_history"):
        summary_parts.append(f"Medical History: {questionnaire_data['medical_history']}")
    
    if questionnaire_data.get("current_medications"):
        summary_parts.append(f"Current Medications: {questionnaire_data['current_medications']}")
    
    return "\n".join(summary_parts) if summary_parts else "No summary available"


def process_questionnaire(questionnaire_data: Dict[str, Any], appointment_id: str) -> Dict[str, Any]:
    """
    Process a pre-visit questionnaire using the pre-visit agent.
    
    Args:
        questionnaire_data: Dictionary containing questionnaire responses
        appointment_id: ID of the associated appointment
        
    Returns:
        Result from the pre-visit agent including summary
    """
    task = f"Process pre-visit questionnaire for appointment {appointment_id}"
    
    context = {
        "action": "process_questionnaire",
        "appointment_id": appointment_id,
        "questionnaire_data": questionnaire_data
    }
    
    logger.info(f"Pre-Visit Agent: Processing questionnaire for appointment {appointment_id}")
    
    # Execute agent task
    result = orchestrator.execute_previsit_task(task, context)
    
    # Generate AI summary
    try:
        summary = summarize_questionnaire(questionnaire_data)
        result["summary"] = summary
        result["summarized"] = True
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        result["summary"] = _create_simple_summary(questionnaire_data)
        result["summarized"] = False
    
    return result

