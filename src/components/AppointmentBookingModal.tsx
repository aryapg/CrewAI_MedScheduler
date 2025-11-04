import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { toast } from "sonner";
import { appointmentsApi } from "@/lib/api-client";
import { useAuth } from "@/hooks/useAuth";

interface AppointmentBookingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  conditionInfo?: {
    condition: string;
    specialty?: string;
  };
}

const AppointmentBookingModal = ({ open, onOpenChange, onSuccess, conditionInfo }: AppointmentBookingModalProps) => {
  const { user } = useAuth();
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [doctor, setDoctor] = useState<string>("");
  const [time, setTime] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [slots, setSlots] = useState<any[]>([]);
  const [slotsLoading, setSlotsLoading] = useState<boolean>(false);

  // Fetch available slots when modal opens or date changes
  useEffect(() => {
    if (open) {
      fetchSlots();
    }
  }, [open, date]);

  const fetchSlots = async () => {
    try {
      setSlotsLoading(true);
      const dateString = date ? date.toISOString().split("T")[0] : undefined;
      const specialty = conditionInfo?.specialty;
      const result = await appointmentsApi.getSlots(undefined, dateString, specialty);
      if (result.data) {
        setSlots(result.data);
      } else if (result.error) {
        setSlots([]);
        toast.error(result.error.includes("HTTP 401") ? "Session expired. Please log in again." : result.error);
      }
    } catch (error) {
      console.error("Error fetching slots:", error);
    } finally {
      setSlotsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!date || !doctor || !time || !user) {
      toast.error("Please fill all fields");
      return;
    }

    setLoading(true);

    try {
      // Parse doctor selection (format: "Dr. Name - Specialty")
      const [doctorName, specialty] = doctor.split(" - ");
      const selectedSlot = slots.find(s => s.doctor_name === doctorName && s.time === time);
      
      if (!selectedSlot) {
        toast.error("Selected slot not found");
        return;
      }

      // Format date as local YYYY-MM-DD to avoid timezone shift
      const yyyy = date.getFullYear();
      const mm = String(date.getMonth() + 1).padStart(2, '0');
      const dd = String(date.getDate()).padStart(2, '0');
      const dateString = `${yyyy}-${mm}-${dd}`;

      const appointmentData = {
        patient_id: user.id,
        doctor_id: selectedSlot.doctor_id || "default",
        doctor_name: doctorName,
        patient_name: user.full_name,
        date: dateString,
        time: time,
        specialty: specialty || "General",
      };

      const result = await appointmentsApi.book(appointmentData);

      if (result.error) {
        toast.error(result.error);
      return;
    }

    toast.success("Appointment booked successfully!");
    onOpenChange(false);
      
      // Reset form
      setDate(new Date());
      setDoctor("");
      setTime("");
      
      // Call success callback
      if (onSuccess) {
        onSuccess();
      } else {
        // Fallback to reload
        window.location.reload();
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to book appointment");
    } finally {
      setLoading(false);
    }
  };

  // Get unique doctors from slots
  const doctors = Array.from(
    new Set(slots.map(slot => `${slot.doctor_name} - ${slot.specialty || "General"}`))
  );

  // Get available times for selected doctor and date
  const selectedDateString = date ? date.toISOString().split("T")[0] : "";
  const availableTimes = slots
    .filter(slot => {
      if (!doctor) return true;
      const [doctorName] = doctor.split(" - ");
      const matchesDoctor = slot.doctor_name === doctorName;
      const matchesDate = !date || slot.date === selectedDateString;
      return matchesDoctor && matchesDate;
    })
    .map(slot => slot.time)
    .filter((time, index, self) => self.indexOf(time) === index)
    .sort(); // Sort times chronologically

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Book New Appointment</DialogTitle>
          <DialogDescription>
            Select your preferred date, time, and doctor
          </DialogDescription>
        </DialogHeader>

        <div className="grid md:grid-cols-2 gap-6 py-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Select Doctor</Label>
              <Select value={doctor} onValueChange={setDoctor}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a doctor" />
                </SelectTrigger>
                <SelectContent>
                  {doctors.length > 0 ? (
                    doctors.map((doc) => (
                    <SelectItem key={doc} value={doc}>
                      {doc}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="loading" disabled>
                      {slotsLoading ? "Loading doctors..." : "No doctors available"}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Select Time</Label>
              <Select value={time} onValueChange={setTime} disabled={!doctor}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a time" />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]">
                  {availableTimes.length > 0 ? (
                    availableTimes.map((slotTime) => {
                      // Check if this slot is available or booked
                      const slotInfo = slots.find(s => 
                        s.doctor_name === doctor.split(" - ")[0] && 
                        s.time === slotTime &&
                        s.date === selectedDateString
                      );
                      const isAvailable = slotInfo?.is_available !== false;
                      
                      return (
                        <SelectItem 
                          key={slotTime} 
                          value={slotTime}
                          disabled={!isAvailable}
                          className={!isAvailable ? "opacity-50" : ""}
                        >
                          {slotTime} {!isAvailable && "(Booked)"}
                        </SelectItem>
                      );
                    })
                  ) : (
                    <SelectItem value="loading" disabled>
                      {!doctor ? "Select a doctor first" : "No available slots"}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              {doctor && availableTimes.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {availableTimes.filter(t => {
                    const s = slots.find(s => s.doctor_name === doctor.split(" - ")[0] && s.time === t && s.date === selectedDateString);
                    return s?.is_available !== false;
                  }).length} available slot(s) for selected doctor
                </p>
              )}
            </div>

            <Button onClick={handleSubmit} className="w-full" disabled={loading}>
              {loading ? "Booking..." : "Confirm Booking"}
            </Button>
          </div>

          <div className="space-y-2">
            <Label>Select Date</Label>
            <Calendar
              mode="single"
              selected={date}
              onSelect={setDate}
              className="rounded-md border"
              disabled={(date) => date < new Date()}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AppointmentBookingModal;
