/**
 * CrewAI Agent Integration Client
 * Handles automatic operations using CrewAI agents
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface CrewAIAutomaticBookingRequest {
  patient_id: string;
  patient_name: string;
  preferred_date?: string;
  preferred_time?: string;
  reason?: string;
  preferred_specialty?: string;
  auto_schedule_reminders?: boolean;
  auto_send_questionnaire?: boolean;
}

export interface CrewAIAutomaticResult {
  success: boolean;
  appointment_id?: string;
  reminder_scheduled?: boolean;
  questionnaire_sent?: boolean;
  agent_results?: any;
  message?: string;
}

/**
 * Automatic appointment booking with CrewAI agents
 * This triggers all agents: booking, reminder, and pre-visit
 */
export async function automaticBookingWithCrewAI(
  request: CrewAIAutomaticBookingRequest
): Promise<CrewAIAutomaticResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/crewai/automatic-booking`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        message: data.detail || data.error || "Automatic booking failed",
      };
    }

    return {
      success: true,
      appointment_id: data.appointment_id,
      reminder_scheduled: data.reminder_scheduled,
      questionnaire_sent: data.questionnaire_sent,
      agent_results: data.agent_results,
      agent_explanation: data.agent_explanation,
      message: data.message || "Automatic booking successful with CrewAI agents",
    };
  } catch (error: any) {
    return {
      success: false,
      message: error.message || "Network error during automatic booking",
    };
  }
}

/**
 * Trigger CrewAI agents for an existing appointment
 */
export async function triggerCrewAIAgentsForAppointment(
  appointmentId: string,
  operations: string[] = ["reminder", "questionnaire"]
): Promise<CrewAIAutomaticResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/crewai/trigger-agents`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
      },
      body: JSON.stringify({
        appointment_id: appointmentId,
        operations,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        message: data.detail || data.error || "Failed to trigger agents",
      };
    }

    return {
      success: true,
      agent_results: data.agent_results,
      message: data.message || "CrewAI agents triggered successfully",
    };
  } catch (error: any) {
    return {
      success: false,
      message: error.message || "Network error",
    };
  }
}

