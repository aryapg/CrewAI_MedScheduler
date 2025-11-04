import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Bell } from "lucide-react";
import { remindersApi } from "@/lib/api-client";
import { useEffect, useState } from "react";

interface NotificationsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const NotificationsModal = ({ open, onOpenChange }: NotificationsModalProps) => {
  const [reminders, setReminders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (open) {
      fetchReminders();
    }
  }, [open]);

  const fetchReminders = async () => {
    setLoading(true);
    try {
      const result = await remindersApi.getLogs();
      if (result.data) {
        setReminders(result.data.reminders || []);
      }
    } catch (error) {
      console.error("Error fetching reminders:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications & Reminders
          </DialogTitle>
          <DialogDescription>Your appointment reminders and notifications</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : reminders.length > 0 ? (
            reminders.map((reminder, idx) => (
              <div key={idx} className="flex items-start gap-3 p-4 rounded-lg border">
                <Bell className="h-5 w-5 text-accent mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="font-medium">
                    Reminder for appointment on {reminder.appointment_date} at {reminder.appointment_time}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {reminder.scheduled_at 
                      ? new Date(reminder.scheduled_at).toLocaleString() 
                      : "Pending"}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Type: {reminder.reminder_type?.toUpperCase() || "SMS"}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              No reminders or notifications yet
            </p>
          )}
        </div>

        <Button onClick={() => onOpenChange(false)} className="w-full">
          Close
        </Button>
      </DialogContent>
    </Dialog>
  );
};

export default NotificationsModal;

