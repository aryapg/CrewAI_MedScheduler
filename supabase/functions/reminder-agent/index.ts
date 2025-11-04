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
      Deno.env.get('SUPABASE_PUBLISHABLE_KEY') ?? '',
      {
        global: {
          headers: { Authorization: req.headers.get('Authorization')! },
        },
      }
    );

    const { data: { user }, error: userError } = await supabaseClient.auth.getUser();
    
    if (userError || !user) {
      console.error('Auth error:', userError);
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const { action, ...payload } = await req.json();
    console.log('Reminder Agent received:', { action, user: user.id });

    // REMINDER AGENT: Manages reminder scheduling and notifications
    switch (action) {
      case 'schedule_reminder': {
        const { appointment_id, reminder_type, scheduled_at, message } = payload;

        // Verify the appointment belongs to user or user is the doctor
        const { data: appointment, error: appointmentError } = await supabaseClient
          .from('appointments')
          .select('*, doctors:doctor_id(user_id)')
          .eq('id', appointment_id)
          .single();

        if (appointmentError || !appointment) {
          return new Response(
            JSON.stringify({ success: false, error: 'Appointment not found' }),
            { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }

        // Create reminder
        const { data: reminder, error: reminderError } = await supabaseClient
          .from('reminders')
          .insert({
            appointment_id,
            reminder_type: reminder_type || 'email',
            scheduled_at,
            message: message || `Reminder: You have an appointment on ${appointment.appointment_date} at ${appointment.appointment_time}`,
            status: 'pending'
          })
          .select()
          .single();

        if (reminderError) throw reminderError;

        console.log('Reminder scheduled:', reminder.id);
        
        // Simulate sending the reminder (in real implementation, use SendGrid/Twilio)
        // For now, immediately mark as sent for demo purposes
        await supabaseClient
          .from('reminders')
          .update({ 
            status: 'sent',
            sent_at: new Date().toISOString()
          })
          .eq('id', reminder.id);

        return new Response(
          JSON.stringify({ 
            success: true, 
            reminder,
            message: 'Reminder scheduled and sent successfully' 
          }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'get_reminders': {
        const { appointment_id } = payload;

        let query = supabaseClient
          .from('reminders')
          .select(`
            *,
            appointments:appointment_id (
              appointment_date,
              appointment_time,
              doctors:doctor_id (
                profiles:user_id (
                  full_name
                )
              )
            )
          `);

        if (appointment_id) {
          query = query.eq('appointment_id', appointment_id);
        }

        const { data: reminders, error } = await query.order('created_at', { ascending: false });

        if (error) throw error;

        console.log('Found reminders:', reminders?.length);
        return new Response(
          JSON.stringify({ success: true, reminders }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'get_reminder_logs': {
        // Get reminder history for user's appointments
        const { data: reminders, error } = await supabaseClient
          .from('reminders')
          .select(`
            *,
            appointments:appointment_id (
              patient_id,
              appointment_date,
              appointment_time,
              doctors:doctor_id (
                user_id,
                profiles:user_id (
                  full_name
                )
              )
            )
          `)
          .order('created_at', { ascending: false })
          .limit(50);

        if (error) throw error;

        console.log('Retrieved reminder logs:', reminders?.length);
        return new Response(
          JSON.stringify({ success: true, logs: reminders }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      default:
        return new Response(
          JSON.stringify({ error: 'Unknown action' }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
    }
  } catch (error: any) {
    console.error('Error in reminder-agent:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
