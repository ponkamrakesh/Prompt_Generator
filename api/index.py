"""
Prompt Alchemist - Full Production Version
Transforms ideas into multiple high-quality styles using Groq API
"""

import os
import sys
import time
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Initialize FastAPI
app = FastAPI(title="Prompt Alchemist")

# Setup paths for Vercel
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama3-70b-8192"
MAX_STYLES = 3

# Style definitions
STYLE_PROMPTS = {
    "cinematic": "Make this cinematic and dramatic with vivid imagery: {}",
    "professional": "Convert to professional business tone: {}",
    "humorous": "Make this funny and witty: {}",
    "analytical": "Break this into logical insights: {}",
    "storytelling": "Turn into creative story with narrative arc: {}",
    "poetic": "Reimagine as lyrical poetry: {}",
    "technical": "Explain with technical precision: {}",
    "minimalist": "Distill to essential meaning only: {}"
}


class GroqClient:
    """Async client for Groq API"""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")
    
    async def transform(self, content: str, styles: List[str], persona: Optional[str] = None) -> List[Dict]:
        """Transform content into multiple styles in parallel"""
        
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
                        "content": f"Error generating {styles[i]} version.",
                        "processing_time": 0.0,
                        "error": str(result)
                    })
                else:
                    processed.append(result)
            
            return processed
    
    async def _call_llm(self, session: aiohttp.ClientSession, style: str, prompt: str) -> Dict:
        """Single LLM call"""
        start = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert writer. Transform content exactly as requested without meta-commentary."},
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
                else:
                    return {
                        "style": style,
                        "content": f"API Error {resp.status}. Please retry.",
                        "processing_time": round(time.time() - start, 2),
                        "error": f"HTTP {resp.status}"
                    }
        except Exception as e:
            return {
                "style": style,
                "content": "Request failed. Please try again.",
                "processing_time": round(time.time() - start, 2),
                "error": str(e)
            }


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
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
    """Process transformation request"""
    
    start_time = time.time()
    
    # Check API key
    if not GROQ_API_KEY:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "show_results": False,
            "error": "API key not configured. Please set GROQ_API_KEY.",
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
    
    # Transform
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
            "error": f"Transformation failed: {str(e)}",
            "original_input": user_input
        })


@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "api_configured": bool(GROQ_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    }


# Vercel handler
handler = app
