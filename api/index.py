"""
Prompt Alchemist - Vercel Compatible Version
"""

import os
import sys
import time
import asyncio
from typing import Optional, List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp

# Create FastAPI app
app = FastAPI(title="Prompt Alchemist")

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Debug: Print paths to verify
print(f"BASE_DIR: {BASE_DIR}")
print(f"STATIC_DIR: {STATIC_DIR}")
print(f"STATIC exists: {os.path.exists(STATIC_DIR)}")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-70b-8192"
MAX_STYLES = 3

STYLE_PROMPTS = {
    "cinematic": "Make this cinematic and dramatic with vivid imagery: {}",
    "professional": "Convert to professional business tone: {}",
    "humorous": "Make this funny and witty: {}",
    "analytical": "Break this into logical insights: {}",
    "storytelling": "Turn into creative story: {}",
    "poetic": "Reimagine as lyrical poetry: {}",
    "technical": "Explain with technical precision: {}",
    "minimalist": "Distill to essential meaning: {}"
}


class GroqClient:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")
    
    async def transform(self, content: str, styles: List[str], persona: Optional[str] = None):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for style in styles:
                prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["professional"]).format(content)
                if persona:
                    prompt = f"Write as {persona}. {prompt}"
                tasks.append(self._call_llm(session, style, prompt))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            processed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed.append({
                        "style": styles[i],
                        "content": f"Error: {str(result)[:50]}",
                        "processing_time": 0.0
                    })
                else:
                    processed.append(result)
            return processed
    
    async def _call_llm(self, session: aiohttp.ClientSession, style: str, prompt: str):
        start = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "Transform content exactly as requested."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }
        try:
            async with session.post(GROQ_API_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return {
                        "style": style,
                        "content": result["choices"][0]["message"]["content"].strip(),
                        "processing_time": round(time.time() - start, 2)
                    }
                return {
                    "style": style,
                    "content": f"Error {resp.status}",
                    "processing_time": round(time.time() - start, 2)
                }
        except Exception as e:
            return {
                "style": style,
                "content": f"Failed: {str(e)[:50]}",
                "processing_time": round(time.time() - start, 2)
            }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "show_results": False
    })


@app.post("/transform", response_class=HTMLResponse)
async def transform(
    request: Request,
    user_input: str = Form(..., min_length=5, max_length=500),
    style_cinematic: bool = Form(False),
    style_professional: bool = Form(False),
    style_humorous: bool = Form(False),
    style_analytical: bool = Form(False),
    style_storytelling: bool = Form(False),
    style_poetic: bool = Form(False),
    style_technical: bool = Form(False),
    style_minimalist: bool = Form(False),
    custom_persona: Optional[str] = Form(None)
):
    start_time = time.time()
    
    if not GROQ_API_KEY:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "show_results": False,
            "error": "GROQ_API_KEY not configured",
            "original_input": user_input
        })
    
    selected = []
    if style_cinematic: selected.append("cinematic")
    if style_professional: selected.append("professional")
    if style_humorous: selected.append("humorous")
    if style_analytical: selected.append("analytical")
    if style_storytelling: selected.append("storytelling")
    if style_poetic: selected.append("poetic")
    if style_technical: selected.append("technical")
    if style_minimalist: selected.append("minimalist")
    
    if not selected:
        selected = ["cinematic", "professional", "storytelling"]
    selected = selected[:MAX_STYLES]
    
    try:
        client = GroqClient()
        results = await client.transform(user_input, selected, custom_persona)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "show_results": True,
            "original_input": user_input,
            "results": results,
            "total_time": round(time.time() - start_time, 2),
            "styles_count": len(selected),
            "custom_persona": custom_persona
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "show_results": False,
            "error": str(e),
            "original_input": user_input
        })


@app.get("/api/health")
async def health():
    return {"status": "healthy", "api_configured": bool(GROQ_API_KEY)}


# CRITICAL: This must be 'app' for ASGI, not 'handler'
# Vercel Python runtime expects 'app' for FastAPI/ASGI applications
