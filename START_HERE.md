# 🚀 Start Here - Run Both Servers

## Quick Start (Easiest Way)

### Windows:
```bash
run-all.bat
```

### Linux/Mac:
```bash
chmod +x run-all.sh
./run-all.sh
```

## Manual Start (Step by Step)

### Step 1: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies (if not already done)
```bash
npm install
```

### Step 3: Create Frontend Environment File

Create `.env.local` in the root directory:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Step 4: Verify Backend Environment

The backend `.env` file should already exist with Firebase credentials. If not, check `backend/.env.example`.

### Step 5: Start Backend Server

**Terminal 1:**
```bash
cd backend
python main.py
```

Wait for: `Application startup complete` or `Uvicorn running on http://0.0.0.0:8000`

### Step 6: Start Frontend Server

**Terminal 2:**
```bash
npm run dev
```

Wait for: `Local: http://localhost:5173`

## 🎉 Access Your Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🧪 Quick Test

1. Open http://localhost:5173
2. Click "Sign Up"
3. Fill in:
   - Full Name: Test User
   - Email: test@example.com
   - Password: password123
4. Click "Sign Up"
5. You should see the Patient Dashboard!

## ✅ Verify Everything Works

1. **Backend Health Check:**
   - Visit: http://localhost:8000/health
   - Should show: `{"status":"healthy"}`

2. **Backend API Docs:**
   - Visit: http://localhost:8000/docs
   - Should see interactive API documentation

3. **Frontend:**
   - Visit: http://localhost:5173
   - Should see login/signup page

## 🐛 Troubleshooting

### Backend Won't Start
- **Python version**: `python --version` (should be 3.8+)
- **Dependencies**: Run `pip install -r backend/requirements.txt`
- **Firebase**: Check `backend/.env` has correct credentials

### Frontend Won't Connect
- **Environment**: Check `.env.local` has `VITE_API_BASE_URL=http://localhost:8000`
- **Backend running**: Verify backend is on http://localhost:8000
- **Browser console**: Check for errors (F12)

### CORS Errors
- Backend CORS should include `http://localhost:5173`
- Check `backend/core/config.py` → `CORS_ORIGINS`

### Authentication Fails
- Clear browser localStorage
- Check backend logs for errors
- Verify JWT secret in `backend/.env`

## 📚 More Information

- **Backend Docs**: `backend/README.md`
- **Quick Start**: `backend/QUICKSTART.md`
- **Integration Guide**: `SETUP_INTEGRATION.md`
- **API Docs**: http://localhost:8000/docs (when backend is running)

---

**Need Help?** Check the logs in both terminal windows for error messages.


