import { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LogOut, Calendar, User, Settings, Bell, ListChecks } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface DashboardLayoutProps {
  children: ReactNode;
  role: "patient" | "doctor" | "admin";
  onNotificationsClick?: () => void;
  onSettingsClick?: () => void;
  onProfileClick?: () => void;
  onAppointmentsClick?: () => void;
}

const DashboardLayout = ({ 
  children, 
  role,
  onNotificationsClick,
  onSettingsClick,
  onProfileClick,
  onAppointmentsClick,
}: DashboardLayoutProps) => {
  const navigate = useNavigate();
  const { signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    navigate("/auth");
  };

  const roleColors = {
    patient: "bg-primary",
    doctor: "bg-accent",
    admin: "bg-destructive",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-secondary/20 to-background">
      {/* Header */}
      <header className="border-b bg-card shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`h-10 w-10 rounded-full ${roleColors[role]} flex items-center justify-center`}>
              <Calendar className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-foreground">MediSchedule</h2>
              <p className="text-xs text-muted-foreground capitalize">{role} Portal</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onAppointmentsClick}
              title="My Appointments"
            >
              <ListChecks className="h-5 w-5" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onNotificationsClick}
              title="Notifications"
            >
              <Bell className="h-5 w-5" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onSettingsClick}
              title="Settings"
            >
              <Settings className="h-5 w-5" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onProfileClick}
              title="Profile"
            >
              <User className="h-5 w-5" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t bg-card mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
          <p>Developed by Aditya Raju and Arya P G — RV University</p>
          <p className="mt-1">MediSchedule v1.0 | Powered by CrewAI Agents | Lovable Cloud</p>
        </div>
      </footer>
    </div>
  );
};

export default DashboardLayout;
