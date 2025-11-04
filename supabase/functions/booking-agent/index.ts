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
    console.log('Booking Agent received:', { action, user: user.id });

    // BOOKING AGENT: Handles appointment slot queries, booking, rescheduling, and cancellation
    switch (action) {
      case 'get_slots': {
        // Fetch available slots
        const { data: slots, error } = await supabaseClient
          .from('appointment_slots')
          .select(`
            *,
            doctors:doctor_id (
              id,
              specialty,
              profiles:user_id (
                full_name
              )
            )
          `)
          .eq('is_available', true)
          .gte('slot_date', new Date().toISOString().split('T')[0])
          .order('slot_date', { ascending: true })
          .order('slot_time', { ascending: true })
          .limit(20);

        if (error) throw error;

        console.log('Found available slots:', slots?.length);
        return new Response(
          JSON.stringify({ success: true, slots }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'book_appointment': {
        const { doctor_id, slot_id, appointment_date, appointment_time, notes } = payload;

        // Check if slot is still available
        const { data: slot, error: slotError } = await supabaseClient
          .from('appointment_slots')
          .select('*')
          .eq('id', slot_id)
          .eq('is_available', true)
          .single();

        if (slotError || !slot) {
          return new Response(
            JSON.stringify({ success: false, error: 'Slot no longer available' }),
            { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }

        // Create appointment
        const { data: appointment, error: appointmentError } = await supabaseClient
          .from('appointments')
          .insert({
            patient_id: user.id,
            doctor_id,
            slot_id,
            appointment_date,
            appointment_time,
            notes: notes || null,
            status: 'confirmed'
          })
          .select()
          .single();

        if (appointmentError) throw appointmentError;

        // Mark slot as unavailable
        await supabaseClient
          .from('appointment_slots')
          .update({ is_available: false })
          .eq('id', slot_id);

        console.log('Appointment booked:', appointment.id);
        return new Response(
          JSON.stringify({ success: true, appointment }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'reschedule_appointment': {
        const { appointment_id, new_slot_id, new_date, new_time } = payload;

        // Verify ownership
        const { data: appointment, error: appointmentError } = await supabaseClient
          .from('appointments')
          .select('*, slot_id')
          .eq('id', appointment_id)
          .eq('patient_id', user.id)
          .single();

        if (appointmentError || !appointment) {
          return new Response(
            JSON.stringify({ success: false, error: 'Appointment not found' }),
            { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }

        // Free up old slot
        await supabaseClient
          .from('appointment_slots')
          .update({ is_available: true })
          .eq('id', appointment.slot_id);

        // Update appointment
        const { data: updated, error: updateError } = await supabaseClient
          .from('appointments')
          .update({
            slot_id: new_slot_id,
            appointment_date: new_date,
            appointment_time: new_time,
          })
          .eq('id', appointment_id)
          .select()
          .single();

        if (updateError) throw updateError;

        // Mark new slot as unavailable
        await supabaseClient
          .from('appointment_slots')
          .update({ is_available: false })
          .eq('id', new_slot_id);

        console.log('Appointment rescheduled:', appointment_id);
        return new Response(
          JSON.stringify({ success: true, appointment: updated }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'cancel_appointment': {
        const { appointment_id } = payload;

        // Verify ownership and get slot
        const { data: appointment, error: appointmentError } = await supabaseClient
          .from('appointments')
          .select('*')
          .eq('id', appointment_id)
          .eq('patient_id', user.id)
          .single();

        if (appointmentError || !appointment) {
          return new Response(
            JSON.stringify({ success: false, error: 'Appointment not found' }),
            { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }

        // Update status to cancelled
        await supabaseClient
          .from('appointments')
          .update({ status: 'cancelled' })
          .eq('id', appointment_id);

        // Free up the slot
        await supabaseClient
          .from('appointment_slots')
          .update({ is_available: true })
          .eq('id', appointment.slot_id);

        console.log('Appointment cancelled:', appointment_id);
        return new Response(
          JSON.stringify({ success: true, message: 'Appointment cancelled' }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'get_my_appointments': {
        const { data: appointments, error } = await supabaseClient
          .from('appointments')
          .select(`
            *,
            doctors:doctor_id (
              specialty,
              profiles:user_id (
                full_name
              )
            )
          `)
          .eq('patient_id', user.id)
          .order('appointment_date', { ascending: true });

        if (error) throw error;

        console.log('Found user appointments:', appointments?.length);
        return new Response(
          JSON.stringify({ success: true, appointments }),
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
    console.error('Error in booking-agent:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
