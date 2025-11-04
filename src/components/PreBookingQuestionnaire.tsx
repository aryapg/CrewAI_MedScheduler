import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface PreBookingQuestionnaireProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: (answers: {
    condition: string;
    urgency: string;
    symptoms?: string;
  }) => void;
}

const PreBookingQuestionnaire = ({ open, onOpenChange, onComplete }: PreBookingQuestionnaireProps) => {
  const [condition, setCondition] = useState("");
  const [urgency, setUrgency] = useState("");
  const [symptoms, setSymptoms] = useState("");

  const handleSubmit = () => {
    if (!condition || !urgency) {
      return;
    }

    onComplete({
      condition,
      urgency,
      symptoms: symptoms || undefined,
    });
    onOpenChange(false);
    
    // Reset form
    setCondition("");
    setUrgency("");
    setSymptoms("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Pre-Booking Questions</DialogTitle>
          <DialogDescription>
            Please answer a few questions to help us find the right doctor for you
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Question 1: Main Condition/Concern */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">
              1. What is your main health concern or condition?
            </Label>
            <Select value={condition} onValueChange={setCondition}>
              <SelectTrigger>
                <SelectValue placeholder="Select your condition" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="heart">Heart/Cardiovascular Issues</SelectItem>
                <SelectItem value="general">General Health Checkup</SelectItem>
                <SelectItem value="neurological">Neurological Issues (Headaches, Seizures, etc.)</SelectItem>
                <SelectItem value="orthopedic">Bone/Joint/Muscle Pain</SelectItem>
                <SelectItem value="skin">Skin Conditions</SelectItem>
                <SelectItem value="pediatric">Child Health Issues</SelectItem>
                <SelectItem value="mental_health">Mental Health Concerns</SelectItem>
                <SelectItem value="cancer">Cancer Screening/Consultation</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Question 2: Urgency */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">
              2. How urgent is your appointment?
            </Label>
            <RadioGroup value={urgency} onValueChange={setUrgency}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="urgent" id="urgent" />
                <Label htmlFor="urgent" className="cursor-pointer">
                  Urgent (Within 24-48 hours)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="soon" id="soon" />
                <Label htmlFor="soon" className="cursor-pointer">
                  Soon (Within a week)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="routine" id="routine" />
                <Label htmlFor="routine" className="cursor-pointer">
                  Routine (Flexible timing)
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Question 3: Symptoms (Optional) */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">
              3. Any specific symptoms you'd like to mention? (Optional)
            </Label>
            <Textarea
              placeholder="Describe your symptoms, duration, or any other relevant information..."
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              rows={4}
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button onClick={handleSubmit} className="flex-1" disabled={!condition || !urgency}>
              Continue to Booking
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

export default PreBookingQuestionnaire;

