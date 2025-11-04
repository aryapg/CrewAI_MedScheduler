"""
Maps patient conditions from pre-booking questionnaire to doctor specialties.
"""

CONDITION_TO_SPECIALTY = {
    "heart": "Cardiologist",
    "general": "General Physician",
    "neurological": "Neurologist",
    "orthopedic": "Orthopedic Surgeon",
    "skin": "Dermatologist",
    "pediatric": "Pediatrician",
    "mental_health": "Psychiatrist",
    "cancer": "Oncologist",
    "other": None  # Show all doctors
}


def get_specialty_for_condition(condition: str) -> str | None:
    """
    Map condition to recommended specialty.
    
    Args:
        condition: Condition from pre-booking questionnaire
        
    Returns:
        Specialty name or None (show all)
    """
    return CONDITION_TO_SPECIALTY.get(condition.lower())

