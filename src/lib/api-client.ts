/**
 * API Client for FastAPI Backend
 * Handles all HTTP requests to the backend API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Token storage key
const TOKEN_STORAGE_KEY = "auth_token";
const USER_STORAGE_KEY = "user_data";

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

/**
 * Get stored auth token
 */
export const getAuthToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_STORAGE_KEY);
};

/**
 * Set auth token
 */
export const setAuthToken = (token: string): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

/**
 * Remove auth token
 */
export const removeAuthToken = (): void => {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
};

/**
 * Get stored user data
 */
export const getUserData = (): any | null => {
  if (typeof window === "undefined") return null;
  const userData = localStorage.getItem(USER_STORAGE_KEY);
  return userData ? JSON.parse(userData) : null;
};

/**
 * Set user data
 */
export const setUserData = (user: any): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
};

/**
 * Base fetch function with authentication
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return {
        error: data.detail || data.message || `HTTP ${response.status}`,
      };
    }

    return { data: data as T };
  } catch (error: any) {
    return {
      error: error.message || "Network error occurred",
    };
  }
}

/**
 * Authentication API
 */
export const authApi = {
  register: async (email: string, password: string, fullName: string, role: string = "patient") => {
    return apiRequest<{ access_token: string; token_type: string; user: any }>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify({ email, password, full_name: fullName, role }),
      }
    );
  },

  login: async (email: string, password: string) => {
    return apiRequest<{ access_token: string; token_type: string; user: any }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }
    );
  },

  getCurrentUser: async () => {
    return apiRequest<any>("/auth/me", {
      method: "GET",
    });
  },
};

/**
 * Appointments API
 */
export const appointmentsApi = {
  getSlots: async (doctorId?: string, date?: string, specialty?: string) => {
    const params = new URLSearchParams();
    if (doctorId) params.append("doctor_id", doctorId);
    if (date) params.append("date", date);
    if (specialty) params.append("specialty", specialty);
    
    return apiRequest<any[]>(
      `/api/slots?${params.toString()}`,
      { method: "GET" }
    );
  },

  book: async (appointmentData: {
    patient_id: string;
    doctor_id: string;
    doctor_name: string;
    patient_name: string;
    date: string;
    time: string;
    reason?: string;
    specialty?: string;
  }) => {
    return apiRequest<any>("/api/book", {
      method: "POST",
      body: JSON.stringify(appointmentData),
    });
  },

  reschedule: async (appointmentId: string, newDate: string, newTime: string, reason?: string) => {
    return apiRequest<any>(`/api/reschedule?appointment_id=${appointmentId}`, {
      method: "PUT",
      body: JSON.stringify({
        new_date: newDate,
        new_time: newTime,
        reason,
      }),
    });
  },

  cancel: async (appointmentId: string, reason?: string) => {
    return apiRequest<{ message: string }>(`/api/cancel?appointment_id=${appointmentId}`, {
      method: "DELETE",
      body: reason ? JSON.stringify({ reason }) : undefined,
    });
  },

  getAll: async () => {
    return apiRequest<any[]>("/api/appointments", {
      method: "GET",
    });
  },
};

/**
 * Reminders API
 */
export const remindersApi = {
  schedule: async (
    appointmentId: string,
    reminderType: string = "sms",
    hoursBefore: number = 24
  ) => {
    return apiRequest<any>("/api/reminder/schedule", {
      method: "POST",
      body: JSON.stringify({
        appointment_id: appointmentId,
        reminder_type: reminderType,
        hours_before: hoursBefore,
      }),
    });
  },

  send: async (appointmentId: string, reminderType: string = "sms") => {
    return apiRequest<any>("/api/reminder/send", {
      method: "POST",
      body: JSON.stringify({
        appointment_id: appointmentId,
        reminder_type: reminderType,
      }),
    });
  },

  getLogs: async (appointmentId?: string) => {
    const params = appointmentId ? `?appointment_id=${appointmentId}` : "";
    return apiRequest<{ reminders: any[]; count: number }>(
      `/api/reminder/logs${params}`,
      { method: "GET" }
    );
  },
};

/**
 * Questionnaires API
 */
export const questionnairesApi = {
  get: async (appointmentId: string) => {
    return apiRequest<any>(`/api/questionnaire/${appointmentId}`, {
      method: "GET",
    });
  },

  submit: async (questionnaireData: {
    appointment_id: string;
    chief_complaint?: string;
    symptoms?: string;
    medical_history?: string;
    current_medications?: string;
    allergies?: string;
    additional_notes?: string;
  }) => {
    return apiRequest<any>("/api/questionnaire/submit", {
      method: "POST",
      body: JSON.stringify(questionnaireData),
    });
  },

  getSummary: async (appointmentId: string) => {
    return apiRequest<{ summary: string }>(
      `/api/questionnaire/appointment/${appointmentId}/summary`,
      { method: "GET" }
    );
  },
};

/**
 * Analytics API
 */
export const analyticsApi = {
  getDashboard: async () => {
    return apiRequest<any>("/api/analytics/dashboard", {
      method: "GET",
    });
  },

  getStats: async (days: number = 30) => {
    return apiRequest<any>(`/api/analytics/stats?days=${days}`, {
      method: "GET",
    });
  },
};

