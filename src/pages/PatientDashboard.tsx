import { useState, useEffect } from "react";
import { Calendar, Clock, FileText, Bell, Bot, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import DashboardLayout from "@/components/DashboardLayout";
import AppointmentBookingModal from "@/components/AppointmentBookingModal";
import QuestionnaireModal from "@/components/QuestionnaireModal";
import RescheduleModal from "@/components/RescheduleModal";
import AppointmentsModal from "@/components/AppointmentsModal";
import NotificationsModal from "@/components/NotificationsModal";
import SettingsModal from "@/components/SettingsModal";
import ProfileModal from "@/components/ProfileModal";
import AgentDecisionModal from "@/components/AgentDecisionModal";
import AgentPreviewModal from "@/components/AgentPreviewModal";
import PreBookingQuestionnaire from "@/components/PreBookingQuestionnaire";
import { appointmentsApi, remindersApi, analyticsApi, questionnairesApi } from "@/lib/api-client";
import { automaticBookingWithCrewAI, triggerCrewAIAgentsForAppointment } from "@/lib/crewai-client";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";

const PatientDashboard = () => {
  const { user } = useAuth();
  const [isBookingOpen, setIsBookingOpen] = useState(false);
  const [isQuestionnaireOpen, setIsQuestionnaireOpen] = useState(false);
  const [isRescheduleOpen, setIsRescheduleOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [isAppointmentsOpen, setIsAppointmentsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isAgentDecisionOpen, setIsAgentDecisionOpen] = useState(false);
  const [isAgentPreviewOpen, setIsAgentPreviewOpen] = useState(false);
  const [isPreBookingOpen, setIsPreBookingOpen] = useState(false);
  const [agentDecisionData, setAgentDecisionData] = useState<any>(null);
  const [agentPreviewData, setAgentPreviewData] = useState<any>(null);
  const [preBookingAnswers, setPreBookingAnswers] = useState<any>(null);
  const [questionnaireInitialData, setQuestionnaireInitialData] = useState<any>(null);
  const [automaticMode, setAutomaticMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [upcomingAppointment, setUpcomingAppointment] = useState<any>(null);
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);
  const [reminders, setReminders] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);

  useEffect(() => {
    if (user) {
      fetchData();
      // Load automatic mode preference from localStorage
      const savedMode = localStorage.getItem("automaticMode");
      if (savedMode !== null) {
        setAutomaticMode(savedMode === "true");
      }
    }
  }, [user]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch appointments - include ALL appointments (manual and automatic)
      const appointmentsResult = await appointmentsApi.getAll();
      if (appointmentsResult.data && appointmentsResult.data.length > 0) {
        const appointments = appointmentsResult.data;
        
        // Filter appointments for current user (if user.id exists)
        const userAppointments = user ? appointments.filter((apt: any) => {
          // Match by patient_id or check if user matches
          return apt.patient_id === user.id || apt.patient_name === user.full_name;
        }) : appointments;
        
        // Sort appointments: confirmed first, then by date/time (newest first for display)
        const sortedAppointments = userAppointments.sort((a: any, b: any) => {
          // Prioritize confirmed appointments
          if (a.status === "confirmed" && b.status !== "confirmed") return -1;
          if (a.status !== "confirmed" && b.status === "confirmed") return 1;
          
          // Then sort by date and time (ascending - earliest first)
          try {
            const dateA = new Date(a.date + " " + (a.time || "00:00"));
            const dateB = new Date(b.date + " " + (b.time || "00:00"));
            return dateA.getTime() - dateB.getTime();
          } catch {
            return 0;
          }
        });
        
        // Get the next upcoming confirmed appointment, or most recent appointment
        const upcoming = sortedAppointments.find((apt: any) => {
          if (apt.status !== "confirmed") return false;
          try {
            const aptDate = new Date(apt.date + " " + (apt.time || "00:00"));
            return aptDate >= new Date();
          } catch {
            return true; // If date parsing fails, include it
          }
        }) || sortedAppointments[0]; // If no future appointment, get the first one
        
        setUpcomingAppointment(upcoming || null);
      } else {
        setUpcomingAppointment(null);
      }

      // Fetch available slots
      let slotsToShow: any[] = [];
      const slotsResult = await appointmentsApi.getSlots();
      if (slotsResult.data) {
        slotsToShow = slotsResult.data;
      }
      // If no slots for today, try tomorrow
      if (!slotsToShow || slotsToShow.length === 0) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const dateString = tomorrow.toISOString().split("T")[0];
        const slotsTomorrow = await appointmentsApi.getSlots(undefined, dateString);
        if (slotsTomorrow.data) {
          slotsToShow = slotsTomorrow.data;
        }
      }
      if (slotsToShow && slotsToShow.length > 0) {
        setAvailableSlots(slotsToShow.slice(0, 5));
      } else {
        setAvailableSlots([]);
      }

      // Fetch reminders
      const remindersResult = await remindersApi.getLogs();
      if (remindersResult.data) {
        setReminders(remindersResult.data.reminders.slice(0, 3));
      }

      // Fetch analytics
      const analyticsResult = await analyticsApi.getDashboard();
      if (analyticsResult.data) {
        setAnalytics(analyticsResult.data);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const handleFillQuestionnaire = async () => {
    if (!upcomingAppointment) {
      toast.error("No appointment found");
      return;
    }

    if (automaticMode) {
      // Automatic mode: Prefill sensible defaults and let user edit before submit
      const defaultsBySpecialty: Record<string, any> = {
        Cardiologist: {
          chief_complaint: upcomingAppointment.reason || "Chest discomfort and shortness of breath",
          symptoms: "Chest tightness on exertion, occasional palpitations, mild fatigue",
          medical_history: "No prior heart attack. Family history of heart disease.",
          current_medications: "None",
          allergies: "None known",
          additional_notes: "Symptoms worsen with stairs; no swelling, no fainting",
        },
        "General Physician": {
          chief_complaint: upcomingAppointment.reason || "General health check-up",
          symptoms: "Low energy and intermittent headaches",
          medical_history: "Seasonal allergies; no chronic illnesses",
          current_medications: "Multivitamin",
          allergies: "Pollen",
          additional_notes: "No recent hospitalizations",
        },
        Dermatologist: {
          chief_complaint: upcomingAppointment.reason || "Itchy rash on forearms",
          symptoms: "Red, dry patches; worse after hot showers",
          medical_history: "No eczema diagnosed previously",
          current_medications: "Moisturizer PRN",
          allergies: "None known",
          additional_notes: "No fever, no discharge",
        },
      };

      const guess = defaultsBySpecialty[upcomingAppointment.specialty || ""] || {
        chief_complaint: upcomingAppointment.reason || "Follow-up consultation",
        symptoms: "Intermittent symptoms related to main concern",
        medical_history: "No significant past medical history",
        current_medications: "None",
        allergies: "None known",
        additional_notes: "",
      };

      setQuestionnaireInitialData(guess);
      setIsQuestionnaireOpen(true);
      // Pass initialData via state by updating the component props below
    } else {
      // Manual mode: Open questionnaire modal
      setIsQuestionnaireOpen(true);
    }
  };

  const handleReschedule = async () => {
    if (!upcomingAppointment) return;
    setIsRescheduleOpen(true);
  };

  const handleScheduleReminder = async () => {
    if (!upcomingAppointment) return;

    try {
      toast.info("Scheduling reminder via Reminder Agent...");
      
      const result = await remindersApi.schedule(
        upcomingAppointment.id,
        "sms",
        24
      );

      if (result.error) {
        toast.error(result.error);
        return;
      }

      // Show agent decision explanation
      const reminderDetails = result.data?.reminder_details || {};
      const contactInfo = reminderDetails.contact_info || 
        (reminderDetails.patient_email ? `Email: ${reminderDetails.patient_email}` : "") +
        (reminderDetails.patient_phone ? `${reminderDetails.patient_email ? " | " : ""}Phone: ${reminderDetails.patient_phone}` : "") ||
        "Not provided";
      
      const reminderMethod = reminderDetails.type === "sms" 
        ? `SMS will be sent to: ${reminderDetails.patient_phone || "your registered phone number"} (Using Twilio/SMS Gateway API in production)`
        : `Email will be sent to: ${reminderDetails.patient_email || "your registered email address"} (Using SMTP/Email service)`;
      
      setAgentDecisionData({
        action: "Schedule Reminder",
        explanation: `Reminder Agent scheduled a ${reminderDetails.type?.toUpperCase() || "SMS"} reminder for your appointment with ${upcomingAppointment.doctor_name} on ${upcomingAppointment.date} at ${upcomingAppointment.time}. The reminder will be sent ${reminderDetails.hours_before || 24} hours before your appointment. ${reminderMethod}`,
        steps: [
          "Reminder Agent received your reminder request",
          `Analyzed appointment details: ${upcomingAppointment.doctor_name} on ${upcomingAppointment.date} at ${upcomingAppointment.time}`,
          `Retrieved your contact information: ${contactInfo}`,
          "Selected optimal reminder time (24 hours before appointment) based on best practices",
          `Configured ${reminderDetails.type?.toUpperCase() || "SMS"} notification channel${reminderDetails.type === "sms" ? " (Twilio API or SMS Gateway)" : " (SMTP/Email service)"}`,
          "Scheduled reminder in the notification system",
          "Reminder will be automatically sent at the scheduled time"
        ],
        reminder_scheduled: true,
        appointment_id: upcomingAppointment.id,
        appointment_date: upcomingAppointment.date,
        appointment_time: upcomingAppointment.time,
        reminder_type: reminderDetails.type || "sms",
        hours_before: reminderDetails.hours_before || 24,
        contact_info: contactInfo,
        patient_email: reminderDetails.patient_email,
        patient_phone: reminderDetails.patient_phone
      });
      setIsAgentDecisionOpen(true);

      toast.success("Reminder scheduled successfully! View details in the popup.");
      await fetchData();
    } catch (error: any) {
      toast.error(error.message || "Failed to schedule reminder");
    }
  };

  // Map condition to specialty
  const conditionToSpecialty: Record<string, string> = {
    heart: "Cardiologist",
    general: "General Physician",
    neurological: "Neurologist",
    orthopedic: "Orthopedic Surgeon",
    skin: "Dermatologist",
    pediatric: "Pediatrician",
    mental_health: "Psychiatrist",
    cancer: "Oncologist",
  };

  const handlePreBookingComplete = async (answers: {
    condition: string;
    urgency: string;
    symptoms?: string;
  }) => {
    setPreBookingAnswers(answers);
    const specialty = conditionToSpecialty[answers.condition];

    if (automaticMode) {
      // Fetch actual available slots before showing preview
      toast.info("Finding best available appointment...");
      
      try {
        // Get tomorrow's date
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const dateString = tomorrow.toISOString().split("T")[0];
        
        // Fetch available slots for the specialty
        const slotsResult = await appointmentsApi.getSlots(undefined, dateString, specialty);
        
        if (slotsResult.data && slotsResult.data.length > 0) {
          const availableSlots = slotsResult.data.filter((s: any) => s.is_available !== false);
          const selectedSlot = availableSlots[0]; // First available slot
          
          if (selectedSlot) {
            setAgentPreviewData({
              action: "Automatic Appointment Booking with CrewAI",
              explanation: `Based on your condition (${answers.condition}), the Booking Agent found available ${specialty || "doctor"}. Reminder and questionnaire will be handled automatically.`,
              appointment_details: {
                doctor: selectedSlot.doctor_name,
                specialty: selectedSlot.specialty || specialty || "General",
                date: selectedSlot.date,
                time: selectedSlot.time,
              },
              reminder_details: {
                type: "email",
                hours_before: 24,
              },
              questionnaire_details: {
                will_send: true,
                questions: [
                  { question: "Chief Complaint", answer: answers.symptoms || answers.condition || "To be filled" },
                  { question: "Symptoms", answer: answers.symptoms || "To be filled by patient" },
                  { question: "Medical History", answer: "To be updated" },
                  { question: "Current Medications", answer: "To be updated" },
                  { question: "Allergies", answer: "To be updated" },
                ],
              },
            });
            setIsAgentPreviewOpen(true);
          } else {
            toast.error("No available slots found. Please try manual booking.");
            setIsBookingOpen(true);
          }
        } else {
          // Fallback if no slots
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          setAgentPreviewData({
            action: "Automatic Appointment Booking with CrewAI",
            explanation: `Based on your condition (${answers.condition}), the Booking Agent will find the best available ${specialty || "doctor"}. Reminder and questionnaire will be handled automatically.`,
            appointment_details: {
              doctor: `Available ${specialty || "doctor"}`,
              specialty: specialty || "General",
              date: tomorrow.toISOString().split("T")[0],
              time: "10:00 AM",
            },
            reminder_details: {
              type: "email",
              hours_before: 24,
            },
            questionnaire_details: {
              will_send: true,
            },
          });
          setIsAgentPreviewOpen(true);
        }
      } catch (error) {
        console.error("Error fetching slots:", error);
        toast.error("Error finding available slots. Using default...");
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        setAgentPreviewData({
          action: "Automatic Appointment Booking with CrewAI",
          explanation: `Based on your condition, the Booking Agent will schedule your appointment.`,
          appointment_details: {
            doctor: `Available ${specialty || "doctor"}`,
            specialty: specialty || "General",
            date: tomorrow.toISOString().split("T")[0],
            time: "10:00 AM",
          },
          reminder_details: {
            type: "email",
            hours_before: 24,
          },
          questionnaire_details: {
            will_send: true,
          },
        });
        setIsAgentPreviewOpen(true);
      }
    } else {
      // Open manual booking with filtered doctors
      setIsBookingOpen(true);
    }
  };

  const handleAutomaticBookingConfirm = async () => {
    if (!user || !preBookingAnswers || !agentPreviewData) return;

    setIsAgentPreviewOpen(false);
    toast.info("Using CrewAI agents for automatic booking...");

    const specialty = conditionToSpecialty[preBookingAnswers.condition];
    const previewDetails = agentPreviewData.appointment_details;

    try {
      const result = await automaticBookingWithCrewAI({
        patient_id: user.id,
        patient_name: user.full_name,
        auto_schedule_reminders: true,
        auto_send_questionnaire: true,
        reason: preBookingAnswers.symptoms || preBookingAnswers.condition,
        preferred_specialty: specialty,
        preferred_date: previewDetails?.date,
        preferred_time: previewDetails?.time,
      });

      if (result.success) {
        // Show agent decision explanation
        if (result.agent_explanation) {
          setAgentDecisionData({
            ...result.agent_explanation,
            appointment_id: result.appointment_id,
          });
          setIsAgentDecisionOpen(true);
        }

        toast.success(
          `Automatic booking successful! Appointment ID: ${result.appointment_id}. ` +
          `Reminder: ${result.reminder_scheduled ? "Scheduled" : "Not scheduled"}. ` +
          `Questionnaire: ${result.questionnaire_sent ? "Sent" : "Not sent"}`
        );
        
        // Refresh data to show new appointment
        await fetchData();
        setPreBookingAnswers(null);
      } else {
        toast.error(result.message || "Automatic booking failed");
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to book automatically");
    }
  };

  const handleAutomaticBookingEdit = () => {
    setIsAgentPreviewOpen(false);
    setIsPreBookingOpen(true);
  };

  if (loading) {
    return (
      <DashboardLayout role="patient">
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout 
      role="patient"
      onNotificationsClick={() => setIsNotificationsOpen(true)}
      onSettingsClick={() => setIsSettingsOpen(true)}
      onProfileClick={() => setIsProfileOpen(true)}
      onAppointmentsClick={() => setIsAppointmentsOpen(true)}
    >
      <div className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Patient Dashboard</h1>
            <p className="text-muted-foreground">Manage your appointments and health records</p>
          </div>
          
          {/* Automatic/Manual Mode Toggle */}
          <div className="flex items-center gap-3 bg-card p-3 rounded-lg border">
            <Bot className="h-5 w-5 text-primary" />
            <div className="flex items-center gap-2">
              <Label htmlFor="automatic-mode" className="cursor-pointer">
                {automaticMode ? "CrewAI Automatic Mode" : "Manual Mode"}
              </Label>
              <Switch
                id="automatic-mode"
                checked={automaticMode}
                onCheckedChange={(checked) => {
                  setAutomaticMode(checked);
                  localStorage.setItem("automaticMode", checked.toString());
                  toast.success(
                    checked 
                      ? "CrewAI Automatic Mode enabled - Agents will handle operations"
                      : "Manual Mode enabled - You handle operations"
                  );
                }}
              />
            </div>
          </div>
        </div>

        {/* Upcoming Appointment */}
        {upcomingAppointment ? (
          <Card className="border-primary/20 shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Next Appointment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-lg">{upcomingAppointment.doctor_name}</p>
                    <p className="text-muted-foreground">{upcomingAppointment.specialty || "General"}</p>
                  </div>
                  <Badge variant="secondary">{upcomingAppointment.status}</Badge>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {upcomingAppointment.date}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {upcomingAppointment.time}
                  </span>
                </div>
                <div className="pt-4 flex gap-2 flex-wrap">
                  <Button size="sm" variant="outline" onClick={handleFillQuestionnaire}>
                    <FileText className="h-4 w-4 mr-2" />
                    {automaticMode ? "Auto Process Questionnaire" : "Fill Questionnaire"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleReschedule}>
                    Reschedule
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleScheduleReminder}>
                    <Bell className="h-4 w-4 mr-2" />
                    Schedule Reminder
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-primary/20 shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                Next Appointment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">No upcoming appointments. Book one now!</p>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-4">
          <Card className="shadow-soft hover:shadow-card transition-shadow">
            <CardHeader>
              <CardTitle>Book New Appointment</CardTitle>
              <CardDescription>
                {automaticMode 
                  ? "Use CrewAI agents for automatic booking" 
                  : "Schedule your next visit with available doctors"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {automaticMode ? (
                <Button onClick={() => setIsPreBookingOpen(true)} className="w-full">
                  <Bot className="h-4 w-4 mr-2" />
                  Automatic Booking (CrewAI)
                </Button>
              ) : (
                <Button onClick={() => setIsPreBookingOpen(true)} className="w-full">
                  <Calendar className="h-4 w-4 mr-2" />
                  Book Appointment
                </Button>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-soft hover:shadow-card transition-shadow">
            <CardHeader>
              <CardTitle>Reminders</CardTitle>
              <CardDescription>Recent notifications and alerts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {reminders.length > 0 ? (
                  reminders.map((reminder, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <Bell className="h-4 w-4 text-accent mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-foreground">
                          Reminder for appointment on {reminder.appointment_date} at {reminder.appointment_time}
                        </p>
                        <p className="text-muted-foreground text-xs">
                          {reminder.scheduled_at ? new Date(reminder.scheduled_at).toLocaleString() : "Pending"}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No reminders yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Available Slots */}
        <Card className="shadow-soft">
          <CardHeader>
            <CardTitle>Available Appointment Slots</CardTitle>
            <CardDescription>Quick booking options for upcoming dates</CardDescription>
          </CardHeader>
          <CardContent>
            {availableSlots.length > 0 ? (
              <div className="grid gap-3">
                {availableSlots.map((slot, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                  >
                    <div>
                      <p className="font-medium">{slot.doctor_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {slot.date} at {slot.time}
                      </p>
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => setIsPreBookingOpen(true)}
                    >
                      {automaticMode ? (
                        <>
                          <Bot className="h-3 w-3 mr-1" />
                          Auto Book
                        </>
                      ) : (
                        <>
                          <Calendar className="h-3 w-3 mr-1" />
                          Book Now
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No available slots at the moment</p>
            )}
          </CardContent>
        </Card>

        {/* CrewAI Status */}
        {automaticMode && (
          <Card className="border-primary/50 bg-primary/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                CrewAI Agents Active
              </CardTitle>
              <CardDescription>
                Your operations are being handled automatically by CrewAI agents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span>Booking Agent: Active</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span>Reminder Agent: Active</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span>Pre-Visit Agent: Active</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Modals */}
      <PreBookingQuestionnaire
        open={isPreBookingOpen}
        onOpenChange={setIsPreBookingOpen}
        onComplete={handlePreBookingComplete}
      />
      <AppointmentBookingModal 
        open={isBookingOpen} 
        onOpenChange={(open) => {
          setIsBookingOpen(open);
          if (!open) {
            setPreBookingAnswers(null); // Reset when closed
          }
        }}
        onSuccess={() => {
          setPreBookingAnswers(null);
          fetchData();
        }}
        conditionInfo={preBookingAnswers ? {
          condition: preBookingAnswers.condition,
          specialty: conditionToSpecialty[preBookingAnswers.condition],
        } : undefined}
      />
      <AgentPreviewModal
        open={isAgentPreviewOpen}
        onOpenChange={setIsAgentPreviewOpen}
        previewData={agentPreviewData}
        onConfirm={handleAutomaticBookingConfirm}
        onEdit={handleAutomaticBookingEdit}
        onUpdatePreview={(updated) => setAgentPreviewData(updated)}
      />
      <QuestionnaireModal
        open={isQuestionnaireOpen}
        onOpenChange={setIsQuestionnaireOpen}
        appointmentId={upcomingAppointment?.id || ""}
        initialData={questionnaireInitialData || undefined}
        onSuccess={fetchData}
      />
      <RescheduleModal
        open={isRescheduleOpen}
        onOpenChange={setIsRescheduleOpen}
        appointmentId={upcomingAppointment?.id || ""}
        currentDate={upcomingAppointment?.date || ""}
        currentTime={upcomingAppointment?.time || ""}
        onSuccess={fetchData}
      />
      <NotificationsModal
        open={isNotificationsOpen}
        onOpenChange={setIsNotificationsOpen}
      />
      <AppointmentsModal
        open={isAppointmentsOpen}
        onOpenChange={setIsAppointmentsOpen}
      />
      <SettingsModal
        open={isSettingsOpen}
        onOpenChange={setIsSettingsOpen}
        automaticMode={automaticMode}
        onModeChange={(mode) => {
          setAutomaticMode(mode);
          localStorage.setItem("automaticMode", mode.toString());
        }}
      />
      <ProfileModal
        open={isProfileOpen}
        onOpenChange={setIsProfileOpen}
      />
      <AgentDecisionModal
        open={isAgentDecisionOpen}
        onOpenChange={setIsAgentDecisionOpen}
        agentData={agentDecisionData}
      />
    </DashboardLayout>
  );
};

export default PatientDashboard;
