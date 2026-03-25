"""
Prompt Alchemist - DEBUG VERSION
"""

import os
import sys
import time
import asyncio
from typing import Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp

app = FastAPI(title="Prompt Alchemist")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
print(f"DEBUG: API Key present: {bool(GROQ_API_KEY)}")
print(f"DEBUG: BASE_DIR: {BASE_DIR}")

STYLE_PROMPTS = {
    "cinematic": "Make this cinematic: {}",
    "professional": "Make this professional: {}",
    "humorous": "Make this funny: {}",
    "analytical": "Analyze this: {}",
    "storytelling": "Make this a story: {}"
}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "show_results": False
    })


@app.post("/transform", response_class=HTMLResponse)
async def transform(request: Request, user_input: str = Form(...)):
    print(f"DEBUG: Received input: {user_input[:50]}")
    print(f"DEBUG: API Key: {GROQ_API_KEY[:10]}..." if GROQ_API_KEY else "DEBUG: NO API KEY")
    
    if not GROQ_API_KEY:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "show_results": False,
            "error": "ERROR: GROQ_API_KEY not set. Go to Vercel Dashboard → Settings → Environment Variables",
            "original_input": user_input
        })
    
    # Simple test without Groq first
    return templates.TemplateResponse("index.html", {
        "request": request,
        "show_results": True,
        "original_input": user_input,
        "results": [
            {"style": "test", "content": f"API Key works! Input: {user_input[:50]}", "processing_time": 0.1}
        ],
        "total_time": 0.1,
        "styles_count": 1
    })


@app.get("/debug")
async def debug():
    return PlainTextResponse(f"""
DEBUG INFO:
API Key Present: {bool(GROQ_API_KEY)}
API Key First 10 chars: {GROQ_API_KEY[:10] if GROQ_API_KEY else 'NONE'}
BASE_DIR: {BASE_DIR}
STATIC_DIR exists: {os.path.exists(STATIC_DIR)}
TEMPLATES_DIR exists: {os.path.exists(TEMPLATES_DIR)}
Files in static/css: {os.listdir(os.path.join(STATIC_DIR, 'css')) if os.path.exists(STATIC_DIR) else 'N/A'}
""")


@app.get("/api/health")
async def health():
    return {"api_configured": bool(GROQ_API_KEY)}
