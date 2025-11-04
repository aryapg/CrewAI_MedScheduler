import { Calendar, Users, Clock, FileText } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";

const DoctorDashboard = () => {
  const todayAppointments = [
    {
      id: 1,
      patient: "John Smith",
      time: "9:00 AM",
      type: "Consultation",
      status: "confirmed",
      questionnaire: true,
    },
    {
      id: 2,
      patient: "Mary Johnson",
      time: "10:30 AM",
      type: "Follow-up",
      status: "confirmed",
      questionnaire: false,
    },
    {
      id: 3,
      patient: "Robert Davis",
      time: "2:00 PM",
      type: "New Patient",
      status: "pending",
      questionnaire: true,
    },
  ];

  const stats = [
    { label: "Today's Appointments", value: "8", icon: Calendar },
    { label: "Total Patients", value: "142", icon: Users },
    { label: "Pending Reviews", value: "3", icon: FileText },
  ];

  return (
    <DashboardLayout role="doctor">
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Doctor Dashboard</h1>
          <p className="text-muted-foreground">Manage your schedule and patient records</p>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-3 gap-4">
          {stats.map((stat, idx) => (
            <Card key={idx} className="shadow-soft hover:shadow-card transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-foreground">{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Today's Schedule */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Today's Schedule
            </CardTitle>
            <CardDescription>March 11, 2024 - Monday</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {todayAppointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col items-center justify-center w-16 h-16 rounded-lg bg-secondary">
                      <span className="text-xs font-medium text-secondary-foreground">
                        {appointment.time.split(" ")[1]}
                      </span>
                      <span className="text-lg font-bold text-primary">
                        {appointment.time.split(" ")[0].split(":")[0]}
                      </span>
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">{appointment.patient}</p>
                      <p className="text-sm text-muted-foreground">{appointment.type}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant={appointment.status === "confirmed" ? "default" : "secondary"}
                        >
                          {appointment.status}
                        </Badge>
                        {appointment.questionnaire && (
                          <Badge variant="outline" className="text-accent border-accent">
                            <FileText className="h-3 w-3 mr-1" />
                            Form Ready
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {appointment.questionnaire && (
                      <Button size="sm" variant="outline">
                        View Form
                      </Button>
                    )}
                    <Button size="sm">Send Reminder</Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-4">
          <Card className="shadow-soft">
            <CardHeader>
              <CardTitle>Weekly Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Monday</span>
                  <span className="font-medium">8 appointments</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tuesday</span>
                  <span className="font-medium">6 appointments</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Wednesday</span>
                  <span className="font-medium">7 appointments</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-soft">
            <CardHeader>
              <CardTitle>Pending Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-2">
                  <div className="h-2 w-2 rounded-full bg-accent mt-2" />
                  <div className="text-sm">
                    <p className="font-medium">Review patient questionnaires</p>
                    <p className="text-muted-foreground">3 forms pending</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="h-2 w-2 rounded-full bg-accent mt-2" />
                  <div className="text-sm">
                    <p className="font-medium">Update patient records</p>
                    <p className="text-muted-foreground">2 records pending</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DoctorDashboard;
