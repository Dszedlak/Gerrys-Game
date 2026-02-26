# Hosting Gerrys-Game on ngrok

This guide explains how to host your frontend and backend on ngrok for external access while maintaining WebSocket and HTTP API connectivity.

## Quick Start

### Prerequisites
- ngrok installed ([https://ngrok.com/download](https://ngrok.com/download))
- Both backend (Flask) and frontend (Vue) running locally
- Free or paid ngrok account

### Step 1: Start Your Local Services

**Terminal 1 - Backend:**
```bash
cd backend
python run.py
```
The backend will run on `http://localhost:5000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run serve
```
The frontend will run on `http://localhost:8080`

### Step 2: Expose Backend with ngrok

**Terminal 3 - ngrok tunnel:**
```bash
ngrok http 5000
```

This gives you output like:
```
Forwarding                    https://xxxx-xx-xxx-xx-xxxx.ngrok.io -> http://localhost:5000
```

Copy this URL (e.g., `https://xxxx-xx-xxx-xx-xxxx.ngrok.io`)

### Step 3: Configure Frontend for ngrok

#### Option A: Auto-update (Recommended)

**Windows (PowerShell):**
```powershell
.\setup-ngrok.ps1 -BackendUrl "https://xxxx-xx-xxx-xx-xxxx.ngrok.io"
```

**Mac/Linux (Bash):**
```bash
chmod +x setup-ngrok.sh
./setup-ngrok.sh "https://xxxx-xx-xxx-xx-xxxx.ngrok.io"
```

#### Option B: Manual Edit

Edit `frontend/.env.local`:
```env
VUE_APP_BACKEND_IP=xxxx-xx-xxx-xx-xxxx.ngrok.io
VUE_APP_BACKEND_PORT=443
VUE_APP_BACKEND_PROTOCOL=https
```

### Step 4: Reload Frontend

After updating `.env.local`, refresh your browser at `http://localhost:8080`. The frontend will now connect to your ngrok backend URL instead of localhost.

## What Was Changed

The app has been configured to use environment variables for backend connectivity:

### Frontend Configuration (`frontend/src/common/config.js`)
```javascript
export const IP_ADDRESS = process.env.VUE_APP_BACKEND_IP || "localhost";
export const BACKEND_PORT = process.env.VUE_APP_BACKEND_PORT || "5000";
export const BACKEND_PROTOCOL = process.env.VUE_APP_BACKEND_PROTOCOL || "http";
export const SOCKET_URL = `${BACKEND_PROTOCOL}://${IP_ADDRESS}:${BACKEND_PORT}`;
```

### WebSocket Connection (`frontend/src/composables/useSocket.js`)
Updated to use the `SOCKET_URL` from config, supporting both HTTP polling and WebSocket transports.

### Backend CORS (`backend/app/__init__.py`)
Already configured with:
```python
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
CORS(app, resources={r"/*": {"origins": "*"}})
```

## Important Notes

⚠️ **Port 443**: ngrok uses HTTPS on port 443 by default. Always use:
- `VUE_APP_BACKEND_PROTOCOL=https`
- `VUE_APP_BACKEND_PORT=443`

⚠️ **Temporary URLs**: Free ngrok accounts get new URLs each time. For production or persistent URLs, use a paid ngrok account with reserved domains.

⚠️ **Environment Variables**: The `.env.local` file is NOT tracked in git. Each developer needs to update it with their ngrok URL, or run the setup script.

## Accessing Your App

- **Locally**: `http://localhost:8080`
- **External (ngrok)**: If you also tunnel the frontend, use its ngrok URL
- **Backend API**: Uses the ngrok backend URL via `VUE_APP_BACKEND_*` environment variables

## Development Workflow

1. Start backend: `python run.py`
2. Start frontend: `npm run serve`
3. Start ngrok: `ngrok http 5000`
4. Update frontend config with ngrok URL
5. Access at `http://localhost:8080` (uses ngrok backend)

## Troubleshooting

**WebSocket connection fails:**
- Make sure ngrok is running
- Check that `BACKEND_PROTOCOL=https` and `BACKEND_PORT=443`
- Verify the ngrok URL is correct in `.env.local`

**CORS errors:**
- Backend already has CORS enabled for all origins (`*`)
- If still issues, check ngrok logs: `ngrok logs`

**Can't connect to backend:**
- Verify backend is running on `localhost:5000`
- Verify ngrok tunnel is active
- Try stopping ngrok and restarting: `ngrok http 5000`

## Adding to .gitignore

If not already present, add to `.gitignore`:
```
frontend/.env.local
frontend/.env.*.local
```

This prevents accidentally committing local ngrok URLs.
