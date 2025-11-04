# Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Navigate to Backend Directory
```bash
cd backend
```

### 2. Create Virtual Environment (Recommended)
**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
The `.env` file is already created with the provided credentials. If you need to modify it:
- Copy `.env.example` to `.env` (already done)
- Update any values if needed

### 5. Run the Server

**Option 1: Using Python directly**
```bash
python main.py
```

**Option 2: Using Uvicorn directly**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using provided scripts**
- Windows: `run.bat`
- Linux/Mac: `chmod +x run.sh && ./run.sh`

### 6. Access the API
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Test the API

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "role": "patient"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

### 3. Get User Info (Protected Route)
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔧 Troubleshooting

### Firebase Connection Issues
- Verify `FIREBASE_PRIVATE_KEY` and `FIREBASE_CLIENT_EMAIL` are correctly set in `.env`
- Check that Firestore is enabled in your Firebase project

### CORS Issues
- Ensure frontend URL is in `CORS_ORIGINS` in `.env`
- Default: `["http://localhost:5173","http://localhost:3000"]`

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version is 3.8+: `python --version`

### Port Already in Use
- Change `PORT` in `.env` to a different port (e.g., 8001)
- Or kill the process using port 8000

## 📚 Next Steps

1. **Test all endpoints** using the interactive docs at `/docs`
2. **Connect your frontend** to `http://localhost:8000`
3. **Check logs** for any errors or warnings
4. **Read the full README.md** for detailed documentation

## 💡 Tips

- Use the interactive API docs at `/docs` for testing endpoints
- All authenticated routes require JWT token in `Authorization: Bearer <token>` header
- CrewAI agents run in mock mode by default (`USE_MOCK_AI=true`)
- Gemini summarization requires `GEMINI_API_KEY` to be set

## 🆘 Need Help?

Check the main `README.md` file for:
- Complete API documentation
- Configuration options
- Advanced setup instructions

