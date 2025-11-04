import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Bot, CheckCircle2, XCircle, Edit, Calendar, Bell, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

interface AgentPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  previewData: {
    action: string;
    appointment_details?: {
      doctor: string;
      specialty: string;
      date: string;
      time: string;
    };
    reminder_details?: {
      type: string;
      hours_before: number;
    };
    questionnaire_details?: {
      will_send: boolean;
      questions?: Array<{ question: string; answer: string }>;
    };
    explanation: string;
  } | null;
  onConfirm: () => void;
  onEdit: () => void;
  onUpdatePreview?: (updated: any) => void;
}

import { useState } from "react";

const AgentPreviewModal = ({ open, onOpenChange, previewData, onConfirm, onEdit, onUpdatePreview }: AgentPreviewModalProps) => {
  if (!previewData) return null;

  const [editing, setEditing] = useState<boolean>(false);
  const [draftQuestions, setDraftQuestions] = useState<Array<{ question: string; answer: string }>>(
    previewData.questionnaire_details?.questions ? [...previewData.questionnaire_details.questions] : []
  );

  const handleAnswerChange = (idx: number, value: string) => {
    const next = [...draftQuestions];
    next[idx] = { ...next[idx], answer: value };
    setDraftQuestions(next);
  };

  const handleSaveEdits = () => {
    const updated = {
      ...previewData,
      questionnaire_details: {
        ...previewData.questionnaire_details,
        will_send: true,
        questions: draftQuestions,
      },
    };
    onUpdatePreview && onUpdatePreview(updated);
    setEditing(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            Preview Agent Actions
          </DialogTitle>
          <DialogDescription>
            Review what the CrewAI agents will do before they proceed
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Main Explanation */}
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Bot className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="font-semibold mb-2">{previewData.action}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{previewData.explanation}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Appointment Details */}
          {previewData.appointment_details && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Appointment Details
                </h3>
                <div className="grid gap-3 p-4 bg-secondary/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Doctor:</span>
                    <p className="text-sm text-muted-foreground flex-1">
                      {previewData.appointment_details.doctor} ({previewData.appointment_details.specialty})
                    </p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Date:</span>
                    <p className="text-sm text-muted-foreground flex-1">{previewData.appointment_details.date}</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-sm font-medium min-w-[100px]">Time:</span>
                    <p className="text-sm text-muted-foreground flex-1">{previewData.appointment_details.time}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Reminder Details */}
          {previewData.reminder_details && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Reminder
                </h3>
                <div className="p-4 bg-secondary/30 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    <Badge variant="outline" className="mr-2">
                      {previewData.reminder_details.type.toUpperCase()}
                    </Badge>
                    Will be sent {previewData.reminder_details.hours_before} hours before appointment
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Questionnaire Details */}
          {previewData.questionnaire_details && (
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Pre-Visit Questionnaire
                </h3>
                <div className="p-4 bg-secondary/30 rounded-lg space-y-3">
                  {editing ? (
                    <div className="space-y-3">
                      {draftQuestions && draftQuestions.length > 0 ? (
                        draftQuestions.map((q, idx) => (
                          <div key={idx} className="p-3 bg-background rounded border text-xs space-y-2">
                            <p className="font-medium">{q.question}</p>
                            <textarea
                              className="w-full border rounded p-2 text-sm"
                              value={q.answer || ""}
                              onChange={(e) => handleAnswerChange(idx, e.target.value)}
                              rows={3}
                            />
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">No questions to edit.</p>
                      )}
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleSaveEdits}>
                          Save Changes
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditing(false)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-muted-foreground mb-3">
                        Questionnaire will be generated automatically with the following details:
                      </p>
                      {previewData.questionnaire_details.questions && (
                        <div className="space-y-2">
                          {previewData.questionnaire_details.questions.map((q: any, idx: number) => (
                            <div key={idx} className="p-2 bg-background rounded border text-xs">
                              <p className="font-medium">{q.question}:</p>
                              <p className="text-muted-foreground">{q.answer || "To be filled"}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button onClick={onConfirm} className="flex-1" size="lg">
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Approve & Continue
            </Button>
            <Button onClick={() => (editing ? handleSaveEdits() : setEditing(true))} variant="outline" size="lg">
              <Edit className="h-4 w-4 mr-2" />
              {editing ? "Save" : "Edit Details"}
            </Button>
            <Button onClick={() => onOpenChange(false)} variant="ghost" size="lg">
              <XCircle className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AgentPreviewModal;

