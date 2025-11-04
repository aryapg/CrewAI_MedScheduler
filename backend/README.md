# Medical Appointment Scheduler Backend

Backend API for Medical Appointment Scheduler using CrewAI, Firestore, and JWT Authentication.

## 🚀 Features

- **FastAPI** - Modern Python web framework
- **CrewAI** - Multi-agent orchestration for booking, reminders, and questionnaires
- **Firebase/Firestore** - Cloud database for users, appointments, reminders, and questionnaires
- **JWT Authentication** - Secure role-based access control (Patient, Doctor, Admin)
- **Gemini AI** - Optional AI summarization for pre-visit questionnaires
- **RESTful API** - Complete CRUD operations for all resources

## 📋 Prerequisites

- Python 3.8+
- Firebase project with Firestore enabled
- (Optional) Gemini API key for AI summarization

## 🛠️ Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
   - Copy `.env.example` to `.env` (already configured with provided credentials)
   - Update values if needed

## 🏃 Running the Server

### Development Mode (with auto-reload):
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Appointments
- `GET /api/slots` - Get available appointment slots
- `POST /api/book` - Book a new appointment
- `PUT /api/reschedule` - Reschedule an appointment
- `DELETE /api/cancel` - Cancel an appointment
- `GET /api/appointments` - Get user's appointments

### Reminders
- `POST /api/reminder/schedule` - Schedule a reminder
- `POST /api/reminder/send` - Send immediate reminder
- `GET /api/reminder/logs` - Get reminder logs

### Questionnaires
- `GET /api/questionnaire/{appointment_id}` - Get questionnaire
- `POST /api/questionnaire/submit` - Submit questionnaire
- `GET /api/questionnaire/appointment/{appointment_id}/summary` - Get AI summary

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard analytics
- `GET /api/analytics/stats` - Get detailed statistics (Doctor/Admin only)

## 🔐 Authentication

All API endpoints (except `/auth/register` and `/auth/login`) require JWT authentication.

Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## 👥 User Roles

- **Patient** - Can book appointments, submit questionnaires, view own data
- **Doctor** - Can view appointments, reminders, questionnaires for their patients
- **Admin** - Full access to all resources

## 🤖 CrewAI Agents

The backend uses CrewAI for automated tasks:

1. **BookingAgent** - Handles appointment booking, rescheduling, and cancellation
2. **ReminderAgent** - Manages appointment reminders via SMS/Email
3. **PreVisitAgent** - Processes pre-visit questionnaires and generates summaries

By default, the backend runs in **mock mode** (`USE_MOCK_AI=true`) for local development. Set `USE_MOCK_AI=false` to use real CrewAI agents.

## 🔥 Firestore Collections

- `users` - User accounts and profiles
- `appointments` - Appointment records
- `reminders` - Reminder schedules and logs
- `questionnaires` - Pre-visit questionnaire responses

## 🤖 Gemini AI Integration

The backend uses Gemini AI (optional) to summarize pre-visit questionnaires. Set `GEMINI_API_KEY` in `.env` to enable this feature.

## 📝 Environment Variables

See `.env.example` for all available configuration options.

## 🧪 Testing

Test the API using:
- FastAPI automatic docs at `/docs`
- Postman/Insomnia
- curl commands

Example curl request:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "patient@example.com", "password": "password123"}'
```

## 🐛 Troubleshooting

1. **Firebase initialization fails**: Check that `FIREBASE_PRIVATE_KEY` and `FIREBASE_CLIENT_EMAIL` are set correctly
2. **CORS errors**: Ensure frontend URL is in `CORS_ORIGINS` in `.env`
3. **JWT token errors**: Check `SECRET_KEY` is set and consistent

## 📄 License

Developed by Aditya Raju and Arya P G

Powered by CrewAI Agents | Firestore Database | FastAPI + Lovable Frontend

