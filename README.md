# Multi-Style Content Generator


Multi-Style Content Generator is a FastAPI web app that transforms one rough input into multiple high-quality writing variations (up to 3 at a time) using the Groq Chat Completions API.

It is designed for deployment on **Vercel** and includes a modern Jinja2 frontend with style selection, advanced persona input, and copy-to-clipboard result cards.

---

## Features

- Transform one prompt into multiple styles in a single run.
- Supports 8 built-in transformation styles:
  - Cinematic
  - Professional
  - Humorous
  - Analytical
  - Storytelling
  - Poetic
  - Technical
  - Minimalist
- Parallel style generation (async) for faster responses.
- Optional custom persona injection (e.g., “Shakespeare”, “Product Manager”).
- Input guardrails:
  - 5–500 characters
  - Max 3 styles per request
- UX enhancements:
  - Loading state on submit
  - Character counter
  - Max-style auto-disabling logic
  - One-click copy for generated text
- Health endpoint for deployment checks.

---

## Tech Stack

- **Backend:** FastAPI, aiohttp, Jinja2
- **Frontend:** HTML templates, vanilla JavaScript, CSS
- **AI Provider:** Groq Chat Completions API
- **Deployment:** Vercel (Python serverless function routing)

---

## Project Structure

```text
.
├── api/
│   ├── __init__.py
│   └── index.py              # FastAPI app, routes, Groq client
├── static/
│   ├── css/
│   │   ├── animations.css
│   │   └── main.css
│   └── js/
│       └── main.js           # Client-side interactions
├── templates/
│   ├── base.html             # Shared page shell
│   └── index.html            # Main UI + results view
├── requirements.txt
├── vercel.json               # Vercel routing config
└── README.md
```

---

## How It Works

1. User submits input text and selects style checkboxes.
2. Backend builds style-specific prompts from `STYLE_PROMPTS`.
3. For each selected style, the app calls Groq asynchronously.
4. Results are rendered in cards with per-style processing time.
5. Users can copy generated output directly.

If no style is selected, the app defaults to:
- `cinematic`
- `professional`
- `storytelling`

---

## API Endpoints

### `GET /`
Renders the main Multi-Style Content Generator UI.

### `POST /transform`
Processes user input and selected styles, then returns generated outputs in HTML.

### `GET /api/health`
Returns deployment health/config status:

```json
{
  "status": "healthy",
  "api_configured": true
}
```

### `GET /debug`
Returns environment/debug diagnostics (API key presence and directory checks).

---

## Environment Variables

Create a `.env` file for local development:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Required:
- `GROQ_API_KEY`: used to authenticate requests to Groq.

---

## Local Development

### 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd Prompt_Generator
```

### 2) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Run the app

```bash
uvicorn api.index:app --reload
```

Then open:

- http://127.0.0.1:8000

---

## Deploy to Vercel

This project is already structured for Vercel Python deployment via `vercel.json` routing.

### Steps

1. Push the repository to GitHub.
2. Import the repository in Vercel.
3. In Vercel Project Settings → Environment Variables, add:
   - `GROQ_API_KEY`
4. Deploy.

### Vercel Routing Behavior

- Requests to `/static/*` are served from static files.
- All other requests are routed to `api/index.py`.

---

## Notes & Limits

- Max transformed styles per request: **3**.
- Current default model in code: `llama-3.1-8b-instant`.
- Groq request timeout is set to 30 seconds per style call.
- If the API key is missing, the UI returns a configuration error instead of calling the model.

---

## Troubleshooting

### "GROQ_API_KEY not configured"
Set `GROQ_API_KEY` in your environment (local `.env` and Vercel env settings).

### Slow or failed generations
- Check Groq API status and quota.
- Reduce concurrent style selections.
- Retry request in case of transient network/API issues.

### Static assets not loading on Vercel
- Confirm `vercel.json` includes the `/static/(.*)` route.
- Ensure `static/` and `templates/` folders are committed.

---

## License

Add your preferred license (e.g., MIT) in a `LICENSE` file if needed.

---

## Acknowledgments

Built with FastAPI + Groq to make prompt transformation simple, fast, and fun.
