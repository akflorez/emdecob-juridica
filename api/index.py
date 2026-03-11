from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import traceback

app = FastAPI(title="Vercel Mount")

backend_app = None
init_error = None

try:
    from backend.main import app as original_app
    backend_app = original_app
    app.mount("/api", backend_app)
except Exception as e:
    init_error = traceback.format_exc()

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all_api(request: Request, full_path: str):
    if init_error:
        return PlainTextResponse(content=f"IMPORT ERROR IN BACKEND (DELAYED):\n\n{init_error}", status_code=500)
    return PlainTextResponse(content="Backend mounted successfully but route not caught by sub-app?", status_code=404)

@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_root_api(request: Request):
    if init_error:
        return PlainTextResponse(content=f"IMPORT ERROR IN BACKEND (DELAYED):\n\n{init_error}", status_code=500)
    return PlainTextResponse(content="Backend API Root", status_code=200)

