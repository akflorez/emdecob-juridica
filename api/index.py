from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Vercel Minimal Test Mount")

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all_api(request: Request, full_path: str):
    return PlainTextResponse(content=f"API is working. Vercel Python container is alive. The crash was inside app.main", status_code=200)

@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_root_api(request: Request):
    return PlainTextResponse(content="API Root working", status_code=200)

