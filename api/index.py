from fastapi import FastAPI
from app.main import app as original_app

# Create a top-level app that mounts the original app under /api
app = FastAPI(title="Vercel Mount")
app.mount("/api", original_app)

# This file is used by Vercel Serverless Functions
# It exposes the FastAPI application instance as 'app'
