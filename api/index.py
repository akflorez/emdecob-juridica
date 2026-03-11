from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
import os
import traceback

app = FastAPI(title="Vercel Mount")

try:
    from app.main import app as original_app
    app.mount("/api", original_app)
except Exception as e:
    err_str = traceback.format_exc()
    @app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def serve_error(full_path: str):
        return PlainTextResponse(content=f"IMPORT ERROR IN BACKEND:\n\n{err_str}", status_code=500)
    
    @app.api_route("/api", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def serve_error_root():
        return PlainTextResponse(content=f"IMPORT ERROR IN BACKEND:\n\n{err_str}", status_code=500)

# Serve the static frontend files
# This is a fallback because Vercel sometimes ignores vercel.json rewrites for monorepos
public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")

if os.path.isdir(public_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(public_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Serve exact file if it exists
        file_path = os.path.join(public_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Otherwise serve index.html for React Router
        index_path = os.path.join(public_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
            
        return {"error": "Frontend build not found"}
else:
    @app.get("/")
    async def serve_root():
        return {"status": "ok", "message": "Backend running, but public frontend not found"}
