import sys
import traceback

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import PlainTextResponse

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

except Exception as outer_e:
    err_str = traceback.format_exc()
    
    # Raw ASGI app fallback to ensure we ALWAYS return something instead of crashing Vercel
    async def app(scope, receive, send):
        if scope['type'] != 'http':
            return
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [
                (b'content-type', b'text/plain'),
            ]
        })
        msg = f"CRITICAL RAW ASGI FALLBACK ERROR:\n\n{err_str}\n\nPYTHONPATH:\n{sys.path}\n"
        await send({
            'type': 'http.response.body',
            'body': msg.encode('utf-8'),
        })

