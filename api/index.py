"""
Prompt Alchemist - Final Working Version
"""

import os
import sys
import time
import asyncio
from typing import Optional, List

# Fix import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp

# App
app = FastAPI(title="Prompt Alchemist")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Mount static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
MAX_STYLES = 3

# Style prompts
STYLE_PROMPTS = {
    "cinematic": (
        "Transform the following content into a vivid, cinematic narrative. 
        Use immersive descriptions, dynamic pacing, emotional depth, and strong visual imagery. 
        Write as if it were a scene from a high-budget film, engaging the reader’s senses.\n\n{}"
    ),

    "professional": (
        "Rewrite the following content in a formal, professional, and polished tone. 
        Ensure clarity, precision, and structured communication suitable for business or expert contexts. 
        Avoid slang and maintain a confident, authoritative voice.\n\n{}"
    ),

    "humorous": (
        "Rewrite the following content to be humorous, witty, and engaging. 
        Incorporate clever wordplay, light sarcasm, or situational humor where appropriate, 
        while keeping it coherent and relevant to the original meaning.\n\n{}"
    ),

    "analytical": (
        "Analyze the following content with a logical and critical approach. 
        Break down key ideas, identify assumptions, evaluate implications, and present clear reasoning. 
        Use structured thinking and, if helpful, organize insights into bullet points.\n\n{}"
    ),

    "storytelling": (
        "Transform the following content into a compelling story. 
        Include a clear narrative arc (setup, conflict, resolution), engaging characters if applicable, 
        and a natural flow that captures attention and evokes emotion.\n\n{}"
    ),

    "poetic": (
        "Rewrite the following content as expressive poetry. 
        Use rhythm, metaphor, imagery, and creative language to evoke emotion and aesthetic depth. 
        Maintain the essence of the original meaning while enhancing artistic expression.\n\n{}"
    ),

    "technical": (
        "Explain the following content in a highly technical and precise manner. 
        Use domain-specific terminology, clear definitions, and structured explanations. 
        Assume the reader has foundational knowledge of the subject.\n\n{}"
    ),

    "minimalist": (
        "Condense the following content into a concise and minimal form. 
        Retain only the most essential information while eliminating redundancy.
        Ensure clarity and brevity without losing meaning.\n\n{}"
    )
}


# =========================
# GROQ CLIENT
# =========================
class GroqClient:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set")
        self.api_key = GROQ_API_KEY

    async def transform(self, content: str, styles: List[str], persona: Optional[str] = None):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for style in styles:
                prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["professional"]).format(content)

                if persona:
                    prompt = f"Write as {persona}.\n\n{prompt}"

                tasks.append(self._call_llm(session, style, prompt))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed.append({
                        "style": styles[i],
                        "content": f"Error: {str(result)}",
                        "processing_time": 0.0
                    })
                else:
                    processed.append(result)

            return processed

    async def _call_llm(self, session, style, prompt):
        start = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "Transform content exactly as requested."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }

        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with session.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            ) as resp:

                text = await resp.text()

                if resp.status == 200:
                    data = await resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    return {
                        "style": style,
                        "content": content.strip() if content else "No response",
                        "processing_time": round(time.time() - start, 2)
                    }

                # show real API error
                return {
                    "style": style,
                    "content": f"Error {resp.status}: {text}",
                    "processing_time": round(time.time() - start, 2)
                }

        except Exception as e:
            return {
                "style": style,
                "content": f"Failed: {str(e)}",
                "processing_time": round(time.time() - start, 2)
            }


# =========================
# ROUTES
# =========================

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

    # Collect styles
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


@app.get("/debug")
async def debug():
    return PlainTextResponse(f"""
DEBUG INFO:
API Key Present: {bool(GROQ_API_KEY)}
API Key First 10 chars: {GROQ_API_KEY[:10] if GROQ_API_KEY else 'NONE'}
BASE_DIR: {BASE_DIR}
STATIC_DIR exists: {os.path.exists(STATIC_DIR)}
TEMPLATES_DIR exists: {os.path.exists(TEMPLATES_DIR)}
""")


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "api_configured": bool(GROQ_API_KEY)
    }
