import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock } from "lucide-react";
import { appointmentsApi } from "@/lib/api-client";

interface AppointmentsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const AppointmentsModal = ({ open, onOpenChange }: AppointmentsModalProps) => {
  const [loading, setLoading] = useState(false);
  const [appointments, setAppointments] = useState<any[]>([]);

  useEffect(() => {
    if (open) {
      loadAppointments();
    }
  }, [open]);

  const loadAppointments = async () => {
    setLoading(true);
    try {
      const res = await appointmentsApi.getAll();
      if (res.data) {
        const sorted = [...res.data].sort((a: any, b: any) => {
          try {
            const dateA = new Date(a.date + " " + (a.time || "00:00")).getTime();
            const dateB = new Date(b.date + " " + (b.time || "00:00")).getTime();
            return dateA - dateB;
          } catch {
            return 0;
          }
        });
        setAppointments(sorted);
      } else {
        setAppointments([]);
      }
    } catch (e) {
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>My Appointments</DialogTitle>
          <DialogDescription>All appointments you have booked</DialogDescription>
        </DialogHeader>

        {loading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : appointments.length > 0 ? (
          <div className="space-y-3">
            {appointments.map((apt: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-4 rounded-lg border border-border">
                <div>
                  <p className="font-medium">{apt.doctor_name} <span className="text-muted-foreground">({apt.specialty || "General"})</span></p>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {apt.date}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {apt.time}
                    </span>
                  </div>
                </div>
                <Badge variant="secondary">{apt.status}</Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No appointments yet</p>
        )}

        <div className="pt-4 flex justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AppointmentsModal;


