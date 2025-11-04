"""
Email service for sending appointment confirmations and reminders.
Uses Gemini AI to generate personalized email content.
Uses SMTP for email delivery.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Mock email sending if not configured
USE_MOCK_EMAIL = settings.USE_MOCK_EMAIL

# Gemini integration for email content generation
gemini_model = None

if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use FREE Gemini model (not pro)
        gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        logger.info("Gemini API initialized successfully for email generation")
    except ImportError:
        logger.warning("google-generativeai not installed. Email content will use templates.")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini for emails: {e}")


def generate_email_content_with_gemini(
    email_type: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    specialty: str,
    reason: Optional[str] = None,
    questionnaire_required: bool = False
) -> Dict[str, str]:
    """
    Generate personalized email subject and body using Gemini AI.
    
    Args:
        email_type: "confirmation" or "reminder"
        patient_name: Patient's full name
        doctor_name: Doctor's full name
        specialty: Doctor's specialty
        appointment_date: Appointment date
        appointment_time: Appointment time
        reason: Reason for appointment (optional)
        questionnaire_required: Whether questionnaire needs to be filled
        
    Returns:
        Dictionary with "subject" and "body" keys
    """
    if gemini_model is None:
        # Fallback to template-based content
        return _get_template_content(
            email_type, patient_name, doctor_name, appointment_date,
            appointment_time, specialty, reason, questionnaire_required
        )
    
    try:
        if email_type == "confirmation":
            prompt = f"""Generate a warm, professional appointment confirmation email for a medical appointment.

Patient Name: {patient_name}
Doctor: {doctor_name} ({specialty})
Date: {appointment_date}
Time: {appointment_time}
Reason: {reason or "General consultation"}
Questionnaire Required: {"Yes - patient needs to fill pre-visit questionnaire" if questionnaire_required else "No"}
Clinic Name: {settings.CLINIC_NAME}
Clinic Phone: {settings.CLINIC_PHONE}

Generate:
1. A clear, friendly subject line (max 60 characters)
2. A professional HTML email body that includes:
   - Warm greeting
   - Confirmation of appointment details
   - Clear appointment information (doctor, date, time, specialty)
   - Instruction to arrive 10 minutes early
   - {("IMPORTANT: Reminder that patient must complete the pre-visit questionnaire in the app before the appointment (do NOT include hyperlinks)." if questionnaire_required else "")}
   - Contact information for changes
   - Clinic contact line with phone number and clinic name
   - Professional closing

Constraints:
- Do NOT include any web links or 'Click here' text. The app is not hosted.
- Use the clinic name "{settings.CLINIC_NAME}" and phone "{settings.CLINIC_PHONE}" instead of placeholders.

Format the response as:
SUBJECT: [subject line]
BODY: [HTML body - use proper HTML formatting with inline styles for email clients]
"""
        else:  # reminder
            prompt = f"""Generate a friendly appointment reminder email for a medical appointment happening in 24 hours.

Patient Name: {patient_name}
Doctor: {doctor_name} ({specialty})
Date: {appointment_date}
Time: {appointment_time}
Reason: {reason or "General consultation"}
Clinic Name: {settings.CLINIC_NAME}
Clinic Phone: {settings.CLINIC_PHONE}

Generate:
1. An urgent but friendly subject line (max 60 characters, mention "tomorrow" or "24 hours")
2. A professional HTML email body that includes:
   - Friendly reminder greeting
   - Clear appointment details (doctor, date, time, specialty)
   - Reminder that appointment is tomorrow/soon
   - Instruction to arrive 10 minutes early
   - Contact information for changes
   - Clinic contact line with phone number and clinic name
   - Professional closing

Constraints:
- Do NOT include any web links or 'Click here' text. The app is not hosted.
- Use the clinic name "{settings.CLINIC_NAME}" and phone "{settings.CLINIC_PHONE}" instead of placeholders.

Format the response as:
SUBJECT: [subject line]
BODY: [HTML body - use proper HTML formatting with inline styles for email clients]
"""
        
        response = gemini_model.generate_content(prompt)
        content = response.text
        
        # Parse response
        subject = ""
        body = ""
        
        lines = content.split("\n")
        in_body = False
        body_lines = []
        
        for line in lines:
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
            elif line.startswith("BODY:"):
                in_body = True
                body_text = line.replace("BODY:", "").strip()
                if body_text:
                    body_lines.append(body_text)
            elif in_body:
                body_lines.append(line)
        
        if subject and body_lines:
            body = "\n".join(body_lines)
            # Post-process to enforce clinic name/phone and remove links
            try:
                import re
                # Replace common placeholders
                body = body.replace("[Your Clinic Name]", settings.CLINIC_NAME)
                body = body.replace("[Your Clinic Phone Number]", settings.CLINIC_PHONE)
                # Replace any 'Click here' prompts with instruction text
                body = re.sub(r"<a[^>]*>(.*?)</a>", r"\\1", body)
                body = re.sub(r"(?i)click here[^.<]*", "Please complete the pre-visit questionnaire in the app before your appointment.", body)
                # Remove Markdown code fences like ```html ... ```
                body = re.sub(r"^```[a-zA-Z]*\s*", "", body.strip())
                body = re.sub(r"```\s*$", "", body)
            except Exception:
                pass
            # Enforce deterministic subjects per email type
            if email_type == "confirmation":
                subject = f"Appointment Booked: {doctor_name} on {appointment_date}"
            else:
                subject = f"24-Hour Reminder: {doctor_name} Appt Tomorrow 🩺"
            logger.info("Email content generated using Gemini AI")
            return {"subject": subject, "body": body}
        else:
            # Fallback if parsing fails
            logger.warning("Failed to parse Gemini response, using template")
            return _get_template_content(
                email_type, patient_name, doctor_name, appointment_date,
                appointment_time, specialty, reason, questionnaire_required
            )
            
    except Exception as e:
        logger.error(f"Error generating email with Gemini: {e}, using template")
        return _get_template_content(
            email_type, patient_name, doctor_name, appointment_date,
            appointment_time, specialty, reason, questionnaire_required
        )


def _get_template_content(
    email_type: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    specialty: str,
    reason: Optional[str] = None,
    questionnaire_required: bool = False
) -> Dict[str, str]:
    """Fallback template-based email content."""
    if email_type == "confirmation":
        subject = f"Appointment Confirmed with {doctor_name} - {appointment_date}"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Appointment Confirmed</h2>
                <p>Dear {patient_name},</p>
                <p>Your appointment has been successfully booked!</p>
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Doctor:</strong> {doctor_name} ({specialty})</p>
                    <p><strong>Date:</strong> {appointment_date}</p>
                    <p><strong>Time:</strong> {appointment_time}</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                </div>
                {"<div style='background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #f59e0b;'><p><strong>📋 Important:</strong> Please complete the pre-visit questionnaire in the app before your appointment. This helps the doctor prepare for your visit.</p></div>" if questionnaire_required else ""}
                <p>Please arrive 10 minutes before your scheduled time.</p>
                <p>If you need to reschedule or cancel, please contact {settings.CLINIC_NAME} at {settings.CLINIC_PHONE} at least 24 hours in advance.</p>
                <p>Best regards,<br>{settings.CLINIC_NAME}</p>
            </div>
        </body>
        </html>
        """
    else:  # reminder
        subject = f"Reminder: Your Appointment Tomorrow with {doctor_name}"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">Appointment Reminder</h2>
                <p>Dear {patient_name},</p>
                <p>This is a reminder that you have an appointment <strong>tomorrow</strong>.</p>
                <div style="background-color: #fef2f2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #dc2626;">
                    <p><strong>Doctor:</strong> {doctor_name} ({specialty})</p>
                    <p><strong>Date:</strong> {appointment_date}</p>
                    <p><strong>Time:</strong> {appointment_time}</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                </div>
                <p>Please arrive 10 minutes before your scheduled time.</p>
                <p>If you need to reschedule or cancel, please contact {settings.CLINIC_NAME} at {settings.CLINIC_PHONE} as soon as possible.</p>
                <p>Best regards,<br>{settings.CLINIC_NAME}</p>
            </div>
        </body>
        </html>
        """
    
    return {"subject": subject, "body": body.strip()}


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if USE_MOCK_EMAIL:
        # Log instead of actually sending
        logger.info(f"[MOCK EMAIL] To: {to_email}")
        logger.info(f"[MOCK EMAIL] Subject: {subject}")
        logger.info(f"[MOCK EMAIL] Body preview: {html_body[:200]}...")
        return True
    
    try:
        # Validate SMTP config
        if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
            logger.error("SMTP is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env or set USE_MOCK_EMAIL=true")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM or settings.SMTP_USER
        msg['To'] = to_email

        msg.attach(MIMEText(text_body or html_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_appointment_confirmation(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    specialty: str,
    reason: Optional[str] = None,
    questionnaire_required: bool = True
) -> bool:
    """
    Send appointment confirmation email to patient.
    Uses Gemini AI to generate personalized content.
    """
    # Generate email content using Gemini
    email_content = generate_email_content_with_gemini(
        email_type="confirmation",
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        specialty=specialty,
        reason=reason,
        questionnaire_required=questionnaire_required
    )
    
    subject = email_content["subject"]
    html_body = email_content["body"]
    
    # Generate plain text version
    import re
    text_body = re.sub('<[^<]+?>', '', html_body)
    
    return send_email(patient_email, subject, html_body, text_body)


def send_appointment_reminder(
    patient_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    specialty: str,
    reason: Optional[str] = None
) -> bool:
    """
    Send appointment reminder email 24 hours before appointment.
    Uses Gemini AI to generate personalized content.
    """
    # Generate email content using Gemini
    email_content = generate_email_content_with_gemini(
        email_type="reminder",
        patient_name=patient_name,
        doctor_name=doctor_name,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        specialty=specialty,
        reason=reason,
        questionnaire_required=False
    )
    
    subject = email_content["subject"]
    html_body = email_content["body"]
    
    # Generate plain text version
    import re
    text_body = re.sub('<[^<]+?>', '', html_body)
    
    return send_email(patient_email, subject, html_body, text_body)
