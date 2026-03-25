"""
Prompt Alchemist - Upgraded High-Level Version
"""

import os
import sys
import time
import asyncio
from typing import Optional, List

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiohttp

# =========================
# APP SETUP
# =========================

app = FastAPI(title="Prompt Alchemist")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# =========================
# CONFIG
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
MAX_STYLES = 3

# =========================
# ELITE STYLE PROMPTS
# =========================

STYLE_PROMPTS = {
    "cinematic": """You are an award-winning film director and screenwriter.

Transform the input into a cinematic scene with:
- Rich sensory details (visual, sound, atmosphere)
- Dramatic pacing and tension
- Emotional depth

Rules:
- Show, don’t tell
- Use present tense
- Make it visually immersive

CONTENT:
{}""",

    "professional": """You are a senior business expert.

Rewrite with:
- Formal, polished tone
- Clear structure and logical flow
- Concise and precise language

Rules:
- No slang
- Maintain authority and clarity

CONTENT:
{}""",

    "humorous": """You are a witty humor writer.

Rewrite to be:
- Clever and engaging
- Lightly sarcastic or playful
- Natural and not forced

Rules:
- Preserve meaning
- Avoid offensive humor

CONTENT:
{}""",

    "analytical": """You are a critical analyst.

Analyze with:
- Logical breakdown
- Assumptions identification
- Implication evaluation

Output Format:
- Key Points
- Analysis
- Insights
- Conclusion

CONTENT:
{}""",

    "storytelling": """You are a master storyteller.

Transform into a narrative with:
- Beginning, development, resolution
- Engaging flow
- Emotional connection

Rules:
- Maintain coherence
- Use vivid but controlled language

CONTENT:
{}""",

    "poetic": """You are a skilled poet.

Rewrite using:
- Rhythm and flow
- Metaphors and imagery
- Emotional depth

Rules:
- Preserve meaning
- Be expressive and artistic

CONTENT:
{}""",

    "technical": """You are a technical expert.

Explain with:
- Precise terminology
- Structured breakdown
- Clear definitions

Output Format:
- Overview
- Detailed Explanation
- Key Concepts

Rules:
- Assume knowledgeable reader

CONTENT:
{}""",

    "minimalist": """You are an expert in concise communication.

Condense into:
- Essential information only
- Clear and direct wording

Rules:
- Remove redundancy
- Maximize information density

CONTENT:
{}"""
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
                    prompt = f"You are {persona}.\n\n{prompt}"

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
                {
                    "role": "system",
                    "content": "Follow the user's transformation instructions strictly. Do not add unrelated content."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 900
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
