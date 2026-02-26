# Single Tunnel Deployment - Quick Start

## For Yourself & Others

### Step 1: Build Frontend (one-time, after code changes)
```powershell
cd frontend
npm run build
cd ..
```

### Step 2: Start Backend (serves everything)
```powershell
cd backend
python run.py
```
Backend will be on `http://localhost:5000` and serving the Vue.js app.

### Step 3: Create ngrok Tunnel (in new terminal)
```powershell
ngrok http 5000
```

### Step 4: Share the ngrok URL
Copy the URL from ngrok output (e.g., `https://xxxxx-xxxxx-xxxxx.ngrok-free.dev`) and share it with others.

---

## For Development (Hot Reload)

If you want to edit code with hot refresh:

### Terminal 1: Frontend (hot reload)
```powershell
cd frontend
npm run serve
```
Runs on `http://localhost:8080`

### Terminal 2: Backend
```powershell
cd backend
python run.py
```
Runs on `http://localhost:5000`

Then update `frontend/.env.local` to point to the backend:
```
VUE_APP_BACKEND_IP=localhost
VUE_APP_BACKEND_PORT=5000
VUE_APP_BACKEND_PROTOCOL=http
```

---

## Key Points

✅ **Production**: Single ngrok URL for everything  
✅ **Development**: Separate dev server + backend for hot reload  
✅ **No configuration needed** for production — it auto-detects the origin  
✅ **One rebuild** per code change, then restart backend  

For detailed info, see `SINGLE_TUNNEL_SETUP.md`
