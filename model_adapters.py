import os
import json
import subprocess
import openai

# ─── OPTIONAL: Claude/Anthropic ────────────────────────────────────────────────
try:
    from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
except ImportError:
    Anthropic = None
    HUMAN_PROMPT = None
    AI_PROMPT = None

# ─── OPTIONAL: Google Gemini/PaLM ──────────────────────────────────────────────
try:
    from google.cloud import aiplatform
    from google.oauth2 import service_account
except ImportError:
    aiplatform = None
    service_account = None

# ─── Groq import and client init ───────────────────────────────────────────────
from groq import Groq
groq_client = Groq()

# ────────────────────────────────────────────────────────────────────────────────
#    Configuration from ENV
# ────────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY   = os.getenv("CLAUDE_API_KEY", "").strip()
GOOGLE_CREDENTIALS  = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

# ─── Init OpenAI ────────────────────────────────────────────────────────────────
openai.api_key = OPENAI_API_KEY
if not openai.api_key:
    print("⚠️ Missing OPENAI_API_KEY – OpenAI calls will fail if used.")

# ─── Init Anthropic ─────────────────────────────────────────────────────────────
if Anthropic and not ANTHROPIC_API_KEY:
    print("⚠️ Missing CLAUDE_API_KEY – Claude calls will fail if used.")

# ─── Init Vertex AI (Gemini) ────────────────────────────────────────────────────
if aiplatform and not GOOGLE_CREDENTIALS:
    print("⚠️ Missing GOOGLE_APPLICATION_CREDENTIALS – Gemini calls will fail if used.")


def call_model(provider: str, prompt: str, **kwargs) -> str:
    provider = provider.lower().strip()

    # ─── OPENAI ────────────────────────────────────────────────────────────────
    if provider == "openai":
        if not openai.api_key:
            raise RuntimeError("OpenAI API key missing.")
        try:
            resp = openai.ChatCompletion.create(
                model=kwargs.get("model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 512),
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to Groq Llama
            print(f"⚠️ OpenAI error: {e}. Falling back to Groq Llama…")
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=True,
                stop=None,
            )
            result = ""
            for chunk in completion:
                text = chunk.choices[0].delta.content or ""
                print(text, end="")  # stream to stdout
                result += text
            return result

    # ─── ANTHROPIC/CLAUDE ────────────────────────────────────────────────────────
    elif provider in ("anthropic", "claude"):
        if Anthropic is None or not ANTHROPIC_API_KEY:
            raise RuntimeError("Anthropic SDK or key missing.")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.completions.create(
            model="claude-v1",
            prompt=HUMAN_PROMPT + prompt + AI_PROMPT,
            max_tokens_to_sample=kwargs.get("max_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.completion.strip()

    # ─── GOOGLE GEMINI/PaLM ─────────────────────────────────────────────────────
    elif provider in ("gemini", "google"):
        if aiplatform is None or not GOOGLE_CREDENTIALS:
            raise RuntimeError("Vertex AI SDK or creds missing.")
        creds  = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS)
        client = aiplatform.gapic.PredictionServiceClient(credentials=creds)
        project_id = os.getenv("GOOGLE_PROJECT_ID", "").strip()
        location   = os.getenv("GOOGLE_LOCATION", "us-central1").strip()
        endpoint   = f"projects/{project_id}/locations/{location}/publishers/google/models/text-bison-001"
        response = client.predict(
            endpoint=endpoint,
            instances=[{"prompt": prompt}],
            parameters={"temperature": kwargs.get("temperature", 0.7), "maxOutputTokens": 512},
        )
        return response.predictions[0].get("content", "").strip()

    else:
        raise ValueError(f"Unknown provider: {provider}")
