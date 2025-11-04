# Integration Setup Guide

## 🚀 Quick Start

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Create Environment File for Frontend

Create a `.env.local` file in the root directory with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Step 3: Run Both Servers

**Windows:**
```bash
run-all.bat
```

**Linux/Mac:**
```bash
chmod +x run-all.sh
./run-all.sh
```

**Or manually:**

Terminal 1 (Backend):
```bash
cd backend
python main.py
```

Terminal 2 (Frontend):
```bash
npm run dev
```

## 🔍 Verification

1. **Backend should be running at:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

2. **Frontend should be running at:**
   - App: http://localhost:5173

## 🧪 Testing the Integration

### 1. Register a New User

1. Open http://localhost:5173
2. Click "Sign Up"
3. Fill in:
   - Full Name: John Doe
   - Email: patient@example.com
   - Password: password123
4. Click "Sign Up"
5. You should be redirected to the Patient Dashboard

### 2. Book an Appointment

1. Click "Book Appointment"
2. Select a doctor, date, and time
3. Click "Confirm Booking"
4. The appointment should appear on your dashboard

### 3. Test Authentication

1. Sign out
2. Sign in with your credentials
3. You should be logged in successfully

## 🐛 Troubleshooting

### Backend Not Starting

- Check Python version: `python --version` (should be 3.8+)
- Verify dependencies: `pip list`
- Check Firebase credentials in `backend/.env`

### Frontend Not Connecting to Backend

- Verify `.env.local` has `VITE_API_BASE_URL=http://localhost:8000`
- Check browser console for CORS errors
- Ensure backend is running on port 8000

### Authentication Issues

- Clear browser localStorage
- Check backend logs for errors
- Verify JWT token is being stored

### CORS Errors

- Ensure backend CORS_ORIGINS includes `http://localhost:5173`
- Check backend `.env` file

## 📝 Notes

- Backend uses mock CrewAI agents by default (`USE_MOCK_AI=true`)
- Firebase/Firestore integration is configured
- JWT tokens are stored in localStorage
- All API endpoints require authentication except `/auth/register` and `/auth/login`


