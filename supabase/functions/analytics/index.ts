import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
    );

    // Get user from request (optional for analytics)
    const authHeader = req.headers.get('Authorization');
    let user = null;
    if (authHeader) {
      const token = authHeader.replace('Bearer ', '');
      const { data } = await supabaseClient.auth.getUser(token);
      user = data.user;
    }

    console.log('Analytics request from:', user?.id || 'anonymous');

    // Get overall statistics
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Total bookings
    const { count: totalBookings } = await supabaseClient
      .from('appointments')
      .select('*', { count: 'exact', head: true });

    // Recent bookings (last 30 days)
    const { count: recentBookings } = await supabaseClient
      .from('appointments')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', thirtyDaysAgo.toISOString());

    // Active patients (unique patients with appointments)
    const { data: activePatients } = await supabaseClient
      .from('appointments')
      .select('patient_id')
      .gte('created_at', thirtyDaysAgo.toISOString());
    
    const uniquePatients = new Set(activePatients?.map(a => a.patient_id)).size;

    // Cancellations
    const { count: cancellations } = await supabaseClient
      .from('appointments')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'cancelled')
      .gte('created_at', thirtyDaysAgo.toISOString());

    // Reminder success rate
    const { count: totalReminders } = await supabaseClient
      .from('reminders')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', thirtyDaysAgo.toISOString());

    const { count: sentReminders } = await supabaseClient
      .from('reminders')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'sent')
      .gte('created_at', thirtyDaysAgo.toISOString());

    const reminderSuccessRate = totalReminders && totalReminders > 0 
      ? Math.round((sentReminders || 0) / totalReminders * 100) 
      : 0;

    // Booking trends (last 7 days)
    const bookingTrends = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      const { count } = await supabaseClient
        .from('appointments')
        .select('*', { count: 'exact', head: true })
        .gte('created_at', dateStr)
        .lt('created_at', new Date(date.getTime() + 24 * 60 * 60 * 1000).toISOString());
      
      bookingTrends.push({
        date: dateStr,
        count: count || 0
      });
    }

    // Recent activity
    const { data: recentAppointments } = await supabaseClient
      .from('appointments')
      .select(`
        *,
        profiles:patient_id (
          full_name
        )
      `)
      .order('created_at', { ascending: false })
      .limit(10);

    const analytics = {
      metrics: {
        totalBookings: totalBookings || 0,
        recentBookings: recentBookings || 0,
        activePatients: uniquePatients,
        cancellations: cancellations || 0,
        reminderSuccessRate: `${reminderSuccessRate}%`
      },
      bookingTrends,
      recentActivity: recentAppointments?.map(apt => ({
        action: apt.status === 'confirmed' ? 'New appointment booked' : 
                apt.status === 'cancelled' ? 'Appointment cancelled' : 
                'Appointment updated',
        user: apt.profiles?.full_name || 'Unknown',
        time: formatTimeAgo(new Date(apt.created_at))
      })) || []
    };

    console.log('Analytics generated successfully');
    return new Response(
      JSON.stringify({ success: true, analytics }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error: any) {
    console.error('Error in analytics:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return `${seconds} seconds ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? 's' : ''} ago`;
}
