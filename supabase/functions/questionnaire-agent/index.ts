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
    console.log('Questionnaire Agent received:', { action, user: user.id });

    // PRE-VISIT QUESTION AGENT: Dispatches medical questionnaires and collects patient responses
    switch (action) {
      case 'get_questionnaire': {
        const { questionnaire_id } = payload;

        if (questionnaire_id) {
          // Get specific questionnaire
          const { data: questionnaire, error } = await supabaseClient
            .from('questionnaires')
            .select('*')
            .eq('id', questionnaire_id)
            .eq('is_active', true)
            .single();

          if (error) throw error;

          return new Response(
            JSON.stringify({ success: true, questionnaire }),
            { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        } else {
          // Get all active questionnaires
          const { data: questionnaires, error } = await supabaseClient
            .from('questionnaires')
            .select('*')
            .eq('is_active', true)
            .order('created_at', { ascending: false });

          if (error) throw error;

          // Return the most recent one or a default general health questionnaire
          const questionnaire = questionnaires?.[0] || {
            id: 'default',
            title: 'Pre-Visit Health Questionnaire',
            description: 'Please answer the following questions before your appointment',
            questions: [
              { id: 'q1', question: 'What is the primary reason for your visit?', type: 'text', required: true },
              { id: 'q2', question: 'Are you currently taking any medications?', type: 'textarea', required: true },
              { id: 'q3', question: 'Do you have any known allergies?', type: 'textarea', required: true },
              { id: 'q4', question: 'Rate your current pain level (0-10)', type: 'number', min: 0, max: 10, required: false },
              { id: 'q5', question: 'Any other symptoms or concerns?', type: 'textarea', required: false }
            ]
          };

          return new Response(
            JSON.stringify({ success: true, questionnaire }),
            { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }
      }

      case 'submit_response': {
        const { appointment_id, questionnaire_id, responses } = payload;

        // Verify the appointment belongs to the user
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

        // Save response
        const { data: response, error: responseError } = await supabaseClient
          .from('questionnaire_responses')
          .upsert({
            appointment_id,
            patient_id: user.id,
            questionnaire_id: questionnaire_id || 'default',
            responses
          }, {
            onConflict: 'appointment_id,questionnaire_id'
          })
          .select()
          .single();

        if (responseError) throw responseError;

        console.log('Questionnaire response submitted:', response.id);
        return new Response(
          JSON.stringify({ 
            success: true, 
            response,
            message: 'Your responses have been saved successfully' 
          }),
          { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        );
      }

      case 'get_responses': {
        const { appointment_id } = payload;

        if (!appointment_id) {
          return new Response(
            JSON.stringify({ success: false, error: 'appointment_id required' }),
            { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
          );
        }

        const { data: responses, error } = await supabaseClient
          .from('questionnaire_responses')
          .select(`
            *,
            questionnaires:questionnaire_id (*),
            appointments:appointment_id (
              appointment_date,
              appointment_time,
              profiles:patient_id (
                full_name
              )
            )
          `)
          .eq('appointment_id', appointment_id);

        if (error) throw error;

        return new Response(
          JSON.stringify({ success: true, responses }),
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
    console.error('Error in questionnaire-agent:', error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
