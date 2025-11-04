import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Edit2 } from "lucide-react";
import { toast } from "sonner";
import { questionnairesApi } from "@/lib/api-client";

interface QuestionnaireModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  appointmentId: string;
  onSuccess?: () => void;
  initialData?: Partial<{
    chief_complaint: string;
    symptoms: string;
    medical_history: string;
    current_medications: string;
    allergies: string;
    additional_notes: string;
  }>;
}

const QuestionnaireModal = ({ open, onOpenChange, appointmentId, onSuccess, initialData }: QuestionnaireModalProps) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    chief_complaint: "",
    symptoms: "",
    medical_history: "",
    current_medications: "",
    allergies: "",
    additional_notes: "",
  });

  // Load existing questionnaire data when modal opens
  useEffect(() => {
    if (open && appointmentId) {
      loadQuestionnaire();
    }
  }, [open, appointmentId]);

  const loadQuestionnaire = async () => {
    try {
      const result = await questionnairesApi.get(appointmentId);
      if (result.data) {
        setFormData({
          chief_complaint: result.data.chief_complaint || "",
          symptoms: result.data.symptoms || "",
          medical_history: result.data.medical_history || "",
          current_medications: result.data.current_medications || "",
          allergies: result.data.allergies || "",
          additional_notes: result.data.additional_notes || "",
        });
      } else if (initialData) {
        // Prefill with agent predictions if provided
        setFormData({
          chief_complaint: initialData.chief_complaint || "",
          symptoms: initialData.symptoms || "",
          medical_history: initialData.medical_history || "",
          current_medications: initialData.current_medications || "",
          allergies: initialData.allergies || "",
          additional_notes: initialData.additional_notes || "",
        });
      }
    } catch (error) {
      // Questionnaire doesn't exist yet, use initialData if provided
      if (initialData) {
        setFormData({
          chief_complaint: initialData.chief_complaint || "",
          symptoms: initialData.symptoms || "",
          medical_history: initialData.medical_history || "",
          current_medications: initialData.current_medications || "",
          allergies: initialData.allergies || "",
          additional_notes: initialData.additional_notes || "",
        });
      }
    }
  };

  const handleSubmit = async () => {
    if (!formData.chief_complaint && !formData.symptoms) {
      toast.error("Please fill at least chief complaint or symptoms");
      return;
    }

    setLoading(true);

    try {
      const result = await questionnairesApi.submit({
        appointment_id: appointmentId,
        ...formData,
      });

      if (result.error) {
        toast.error(result.error);
        return;
      }

      // Show what was submitted
      const submittedData = {
        "Chief Complaint": formData.chief_complaint || "Not provided",
        "Symptoms": formData.symptoms || "Not provided",
        "Medical History": formData.medical_history || "Not provided",
        "Current Medications": formData.current_medications || "Not provided",
        "Allergies": formData.allergies || "Not provided",
        "Additional Notes": formData.additional_notes || "Not provided",
      };

      toast.success(
        <div className="space-y-1">
          <p className="font-semibold">Questionnaire submitted successfully!</p>
          <p className="text-xs">Pre-Visit Agent is processing your responses...</p>
        </div>,
        { duration: 5000 }
      );

      // Show summary of what was submitted
      setTimeout(() => {
        const summaryText = Object.entries(submittedData)
          .filter(([_, value]) => value !== "Not provided")
          .map(([key, value]) => `${key}: ${value}`)
          .join("\n");
        
        if (summaryText) {
          toast.info(
            <div className="space-y-1">
              <p className="font-semibold text-xs">Your Responses:</p>
              <pre className="text-xs whitespace-pre-wrap max-h-32 overflow-y-auto">{summaryText}</pre>
            </div>,
            { duration: 8000 }
          );
        }
      }, 1000);

      onOpenChange(false);
      
      // Reset form
      setFormData({
        chief_complaint: "",
        symptoms: "",
        medical_history: "",
        current_medications: "",
        allergies: "",
        additional_notes: "",
      });

      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to submit questionnaire");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit2 className="h-5 w-5" />
            Pre-Visit Questionnaire
          </DialogTitle>
          <DialogDescription>
            {formData.chief_complaint || formData.symptoms 
              ? "Edit your questionnaire details (filled by agent or previously)"
              : "Please fill out this questionnaire before your appointment"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {(formData.chief_complaint || formData.symptoms) && (
            <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
              <p className="text-xs font-medium text-primary mb-1">Agent-Filled Data Detected</p>
              <p className="text-xs text-muted-foreground">
                You can review and edit the details filled by the Pre-Visit Agent below.
              </p>
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="chief_complaint">Chief Complaint *</Label>
            <Textarea
              id="chief_complaint"
              placeholder="What is the main reason for your visit?"
              value={formData.chief_complaint}
              onChange={(e) => setFormData({ ...formData, chief_complaint: e.target.value })}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="symptoms">Symptoms</Label>
            <Textarea
              id="symptoms"
              placeholder="Describe your symptoms"
              value={formData.symptoms}
              onChange={(e) => setFormData({ ...formData, symptoms: e.target.value })}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="medical_history">Medical History</Label>
            <Textarea
              id="medical_history"
              placeholder="Any relevant medical history"
              value={formData.medical_history}
              onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="medications">Current Medications</Label>
            <Input
              id="medications"
              placeholder="List current medications"
              value={formData.current_medications}
              onChange={(e) => setFormData({ ...formData, current_medications: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="allergies">Allergies</Label>
            <Input
              id="allergies"
              placeholder="List any allergies"
              value={formData.allergies}
              onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Additional Notes</Label>
            <Textarea
              id="notes"
              placeholder="Any additional information"
              value={formData.additional_notes}
              onChange={(e) => setFormData({ ...formData, additional_notes: e.target.value })}
              rows={3}
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button onClick={handleSubmit} disabled={loading} className="flex-1">
              {loading ? "Submitting..." : "Submit Questionnaire"}
            </Button>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default QuestionnaireModal;

