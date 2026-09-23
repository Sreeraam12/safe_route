"""
SafeRoute Backend Server Launcher
=================================
Binds to 0.0.0.0:8000 so the backend is accessible from localhost, 127.0.0.1,
and across the local network (LAN IP, mobile devices, etc.).
"""

import uvicorn

if __name__ == "__main__":
    print("=================================================================")
    print("  Starting SafeRoute Backend Server on http://0.0.0.0:8000")
    print("  Accessible via:")
    print("    - http://localhost:8000")
    print("    - http://127.0.0.1:8000")
    print("    - http://<YOUR_LAN_IP>:8000 (from phone / external device)")
    print("=================================================================")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

