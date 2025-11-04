import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  automaticMode: boolean;
  onModeChange: (automatic: boolean) => void;
}

const SettingsModal = ({ open, onOpenChange, automaticMode, onModeChange }: SettingsModalProps) => {
  const handleModeToggle = (checked: boolean) => {
    onModeChange(checked);
    toast.success(checked ? "Automatic mode enabled with CrewAI agents" : "Manual mode enabled");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>Manage your application preferences</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="automatic-mode">Automatic Mode (CrewAI)</Label>
              <p className="text-sm text-muted-foreground">
                Enable CrewAI agents to automatically handle booking, reminders, and questionnaires
              </p>
            </div>
            <Switch
              id="automatic-mode"
              checked={automaticMode}
              onCheckedChange={handleModeToggle}
            />
          </div>

          <div className="pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              <strong>Automatic Mode:</strong> CrewAI agents will automatically book appointments, 
              schedule reminders, and process questionnaires.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              <strong>Manual Mode:</strong> You handle all operations manually.
            </p>
          </div>

          <Button onClick={() => onOpenChange(false)} className="w-full">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsModal;

