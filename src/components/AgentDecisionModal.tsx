import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Bot, CheckCircle2, Clock, FileText, Calendar, Bell } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

interface AgentDecisionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentData: {
    action: string;
    explanation: string;
    steps: string[];
    result?: any;
    appointment_id?: string;
    slot_selected?: {
      doctor: string;
      date: string;
      time: string;
      reason: string;
    };
    reminder_scheduled?: boolean;
    questionnaire_data?: {
      questions: Array<{ question: string; answer: string }>;
      summary?: string;
    };
    appointment_date?: string;
    appointment_time?: string;
    reminder_type?: string;
    hours_before?: number;
  } | null;
}

const AgentDecisionModal = ({ open, onOpenChange, agentData }: AgentDecisionModalProps) => {
  if (!agentData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl">
            <Bot className="h-6 w-6 text-primary" />
            CrewAI Agent Decision Process
          </DialogTitle>
          <DialogDescription>
            Detailed explanation of how the CrewAI agents made their decisions
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Main Explanation */}
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-2">{agentData.action}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{agentData.explanation}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Steps Taken */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Process Steps
            </h3>
            <div className="space-y-2">
              {agentData.steps.map((step, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-secondary/50 rounded-lg border">
                  <Badge variant="outline" className="mt-0.5 min-w-[2rem] justify-center">
                    {idx + 1}
                  </Badge>
                  <p className="text-sm flex-1 leading-relaxed">{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Slot Selection Details */}
          {agentData.slot_selected && (
            <Card className="border-t pt-4">
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Appointment Details Selected by Agent
                </h3>
                <div className="grid gap-3 p-4 bg-secondary/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Doctor:</span>
                    <p className="text-sm text-muted-foreground flex-1">{agentData.slot_selected.doctor}</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Date:</span>
                    <p className="text-sm text-muted-foreground flex-1">{agentData.slot_selected.date}</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Time:</span>
                    <p className="text-sm text-muted-foreground flex-1">{agentData.slot_selected.time}</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Reason:</span>
                    <p className="text-sm text-muted-foreground flex-1">{agentData.slot_selected.reason || "Not specified"}</p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-3 italic">
          The agent analyzed available slots and selected this based on doctor availability and your preferences.
        </p>
              </CardContent>
            </Card>
          )}

          {/* Reminder Status */}
          {agentData.reminder_scheduled !== undefined && (
            <Card className="border-t pt-4">
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Reminder Status
                </h3>
                <div className="p-4 bg-secondary/30 rounded-lg">
                  <Badge variant={agentData.reminder_scheduled ? "default" : "secondary"} className="mb-2">
                    {agentData.reminder_scheduled ? "✓ Scheduled" : "✗ Not Scheduled"}
                  </Badge>
                  {agentData.reminder_scheduled && (
                    <div className="mt-3 space-y-2 text-sm">
                      <p className="text-muted-foreground">
                        <span className="font-medium">Type:</span> {agentData.reminder_type?.toUpperCase() || "SMS"}
                      </p>
                      <p className="text-muted-foreground">
                        <span className="font-medium">Timing:</span> {agentData.hours_before || 24} hours before appointment
                      </p>
                      {agentData.appointment_date && (
                        <p className="text-muted-foreground">
                          <span className="font-medium">For:</span> {agentData.appointment_date} at {agentData.appointment_time}
                        </p>
                      )}
                      {agentData.contact_info && (
                        <div className="p-2 bg-primary/10 rounded border border-primary/20">
                          <p className="text-xs font-medium mb-1">Reminder Delivery:</p>
                          <p className="text-xs text-muted-foreground">{agentData.contact_info}</p>
                          {agentData.patient_email && (
                            <p className="text-xs text-muted-foreground mt-1">
                              📧 Email: {agentData.patient_email}
                            </p>
                          )}
                          {agentData.patient_phone && (
                            <p className="text-xs text-muted-foreground">
                              📱 Phone: {agentData.patient_phone}
                            </p>
                          )}
                          <p className="text-xs text-muted-foreground italic mt-2">
                            {agentData.reminder_type === "sms" 
                              ? "💡 SMS reminders use Twilio API or SMS Gateway service in production"
                              : "💡 Email reminders use SMTP/Email service (e.g., SendGrid, AWS SES)"}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                  <p className="text-sm text-muted-foreground mt-3">
                    {agentData.reminder_scheduled
                      ? "Reminder Agent scheduled the notification to ensure you don't miss your appointment."
                      : "Reminder was not scheduled automatically. You can schedule one manually."}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Questionnaire Details */}
          {agentData.questionnaire_data && (
            <Card className="border-t pt-4">
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Pre-Visit Questionnaire Details
                </h3>
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground mb-3">
                    The Pre-Visit Agent generated the following questions for your appointment:
                  </p>
                  {agentData.questionnaire_data.questions.map((item, idx) => (
                    <div key={idx} className="p-4 bg-secondary/30 rounded-lg border">
                      <p className="font-medium text-sm mb-1">{item.question}</p>
                      <p className="text-sm text-muted-foreground">{item.answer || "Not provided"}</p>
                    </div>
                  ))}
                  {agentData.questionnaire_data.summary && (
                    <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                      <p className="font-medium text-sm mb-2">AI-Generated Summary (Gemini AI):</p>
                      <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                        {agentData.questionnaire_data.summary}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Appointment ID */}
          {agentData.appointment_id && (
            <div className="border-t pt-4">
              <p className="text-sm">
                <span className="font-medium">Appointment ID:</span>{" "}
                <code className="bg-secondary px-2 py-1 rounded text-xs font-mono">
                  {agentData.appointment_id}
                </code>
              </p>
            </div>
          )}

          <Button onClick={() => onOpenChange(false)} className="w-full">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AgentDecisionModal;
