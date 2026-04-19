"""
LLM Module — Phi-3-mini with optional LoRA adapter.

When USE_DUMMY_AI=true in .env, a structured dummy response is returned
so you can develop/test the platform without a GPU.
"""
import os
import json
import logging

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

USE_DUMMY_AI = os.getenv("USE_DUMMY_AI", "true").lower() == "true"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("MODEL_NAME", "phi3.5:latest"))
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))


def generate_response(prompt: str) -> str:
    """Generate text from Ollama. Uses dummy data if USE_DUMMY_AI=true."""
    if USE_DUMMY_AI:
        return _dummy_response()

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 512,
        },
    }

    try:
        logger.info("Generating response with Ollama model '%s'", OLLAMA_MODEL)
        response = httpx.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=payload,
            timeout=httpx.Timeout(OLLAMA_TIMEOUT, connect=10.0),
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()
    except httpx.HTTPError as exc:
        logger.error("Ollama generation failed: %s", exc)
        raise RuntimeError(
            f"Could not reach Ollama model '{OLLAMA_MODEL}'. "
            "Make sure Ollama is running and the model is installed."
        ) from exc


def repair_json_response(raw_text: str) -> str:
    """Ask the local model to convert raw output into valid JSON only."""
    if USE_DUMMY_AI:
        return _dummy_response()

    repair_prompt = f"""Convert the following text into one valid JSON object only.

Required keys:
- feasibility
- cost_breakdown
- roadmap
- marketing
- risks
- competitors
- funding
- idea_score
- stage

Rules:
- Return JSON only
- roadmap, marketing, risks, competitors, funding must be arrays of strings
- idea_score must be an integer from 0 to 100
- stage must be a short string

Text to convert:
{raw_text}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": repair_prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 384,
        },
    }

    try:
        logger.info("Repairing invalid JSON with Ollama model '%s'", OLLAMA_MODEL)
        response = httpx.post(
            f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json=payload,
            timeout=httpx.Timeout(OLLAMA_TIMEOUT, connect=10.0),
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()
    except httpx.HTTPError as exc:
        logger.error("Ollama JSON repair failed: %s", exc)
        return ""


def _dummy_response() -> str:
    """Structured JSON dummy response for development/testing."""
    return json.dumps({
        "feasibility": (
            "This business idea shows strong potential. The market demand is validated "
            "by current industry trends and consumer behavior. Execution feasibility is "
            "medium-high — the main challenge lies in initial customer acquisition, "
            "which can be addressed with targeted digital marketing."
        ),
        "cost_breakdown": (
            "Estimated startup costs: Registration & Legal ₹15,000 | Website & Tech ₹25,000 | "
            "Marketing (first 3 months) ₹30,000 | Operations & Inventory ₹50,000 | "
            "Miscellaneous ₹10,000. Total estimated: ₹1,30,000."
        ),
        "roadmap": [
            "Month 1: Legal registration, brand identity, website development",
            "Month 2: Soft launch, onboard first 10 customers, gather feedback",
            "Month 3: Refine product/service based on feedback, ramp up marketing",
            "Month 4-6: Scale operations, explore B2B partnerships",
            "Month 7-12: Target breakeven, launch referral program"
        ],
        "marketing": [
            "Leverage Instagram Reels and YouTube Shorts for organic reach",
            "Partner with local micro-influencers for trust-building",
            "Offer a freemium or trial tier to reduce entry barrier",
            "Build an email list from day one using lead magnets",
            "List on Google My Business for local discoverability"
        ],
        "risks": [
            "High competition from established players — mitigate with niche focus",
            "Cash flow issues in early months — maintain 3-month operating reserve",
            "Customer acquisition cost may exceed projections — A/B test ad creatives",
            "Regulatory changes — consult a local legal advisor quarterly"
        ],
        "competitors": [
            "Market Leader Corp — strong brand but poor customer service",
            "StartupX — tech-forward but expensive pricing",
            "LocalPro — limited to metro cities, your opportunity in Tier-2"
        ],
        "funding": [
            "Bootstrapping — ideal for MVP stage with ₹1-2L budget",
            "Startup India Seed Fund — up to ₹50L for registered startups",
            "Angel investors via platforms like LetsVenture or AngelList India",
            "SIDBI CGTMSE loan — collateral-free up to ₹10L for new businesses"
        ],
        "idea_score": 74,
        "stage": "MVP"
    })
