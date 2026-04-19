"""
RAG Pipeline
-------------
1. Embed the user's business idea + question
2. Retrieve top-k relevant chunks from ChromaDB
3. Build a structured prompt
4. Pass to Ollama (or dummy LLM) and return parsed JSON
"""
import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

USE_DUMMY_AI = os.getenv("USE_DUMMY_AI", "true").lower() == "true"


def build_prompt(
    idea_title: str,
    idea_description: str,
    budget: str,
    location: str,
    category: str,
    experience_level: str,
    context_chunks: list,
) -> str:
    context_text = "\n\n".join(context_chunks) if context_chunks else "No additional context available."

    return f"""You are GrowthPilot, an expert AI business mentor helping entrepreneurs evaluate and plan business ideas.

Return only a valid JSON object with these exact keys:
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
- roadmap, marketing, risks, competitors, and funding must be JSON arrays of strings
- idea_score must be an integer between 0 and 100
- stage must be a short string such as Idea, MVP, Growth, or Scale
- do not include markdown, code fences, or extra explanation outside the JSON

Business knowledge context:
{context_text}

Business idea:
Title: {idea_title}
Description: {idea_description}
Budget: {budget or "Not specified"}
Location: {location or "Not specified"}
Category: {category or "General"}
Founder experience: {experience_level or "Beginner"}
"""


def analyze_idea(
    idea_title: str,
    idea_description: str,
    budget: str = None,
    location: str = None,
    category: str = None,
    experience_level: str = "beginner",
) -> dict:
    """
    Full RAG pipeline:
    1. Embed idea
    2. Retrieve from ChromaDB
    3. Generate with LLM
    4. Parse and return structured dict
    """

    context_chunks = []

    if not USE_DUMMY_AI:
        try:
            from ai_engine.embeddings import embed_text
            from ai_engine.vector_store import query_similar

            query = f"{idea_title}. {idea_description}"
            query_embedding = embed_text(query)
            context_chunks = query_similar(query_embedding, n_results=5)
            logger.info("Retrieved %s context chunks from ChromaDB.", len(context_chunks))
        except Exception as exc:
            logger.warning("RAG retrieval unavailable, continuing without context: %s", exc)

    prompt = build_prompt(
        idea_title,
        idea_description,
        budget,
        location,
        category,
        experience_level,
        context_chunks,
    )

    from ai_engine.llm import generate_response

    raw_output = generate_response(prompt)
    return _parse_output(raw_output)


def _parse_output(raw: str) -> dict:
    """Extract and parse JSON from model output."""
    try:
        return _normalize_output(json.loads(raw))
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return _normalize_output(json.loads(match.group()))
            except json.JSONDecodeError:
                pass

    try:
        from ai_engine.llm import repair_json_response

        repaired = repair_json_response(raw)
        if repaired:
            try:
                return _normalize_output(json.loads(repaired))
            except json.JSONDecodeError:
                import re

                match = re.search(r"\{.*\}", repaired, re.DOTALL)
                if match:
                    return _normalize_output(json.loads(match.group()))
    except Exception as exc:
        logger.warning("JSON repair attempt failed: %s", exc)

    logger.error("Failed to parse JSON from LLM output. Using fallback.")
    return {
        "feasibility": "Analysis complete. Please review the details.",
        "cost_breakdown": "Cost breakdown not available. Please refine your inputs.",
        "roadmap": ["Define MVP", "Build & test", "Launch", "Scale"],
        "marketing": ["Social media", "Word of mouth", "Content marketing"],
        "risks": ["Market risk", "Financial risk", "Execution risk"],
        "competitors": ["Research competitors in your niche"],
        "funding": ["Bootstrapping", "Angel investors", "Government grants"],
        "idea_score": 60,
        "stage": "Idea",
    }


def _normalize_output(data: dict) -> dict:
    """Coerce model output into the schema expected by the app."""
    return {
        "feasibility": _stringify_value(data.get("feasibility")),
        "cost_breakdown": _stringify_value(data.get("cost_breakdown")),
        "roadmap": _normalize_list(data.get("roadmap")),
        "marketing": _normalize_list(data.get("marketing")),
        "risks": _normalize_list(data.get("risks")),
        "competitors": _normalize_list(data.get("competitors")),
        "funding": _normalize_list(data.get("funding")),
        "idea_score": _normalize_score(data.get("idea_score")),
        "stage": _stringify_value(data.get("stage")) or "Idea",
    }


def _normalize_list(value) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        text = _stringify_value(value)
        return [text] if text else []
    items = []
    for item in value:
        text = _stringify_value(item)
        if text:
            items.append(text)
    return items


def _normalize_score(value) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = 60
    return max(0, min(100, score))


def _stringify_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            parts.append(f"{key}: {_stringify_value(item)}")
        return ", ".join(part for part in parts if part.strip())
    if isinstance(value, list):
        return ", ".join(
            part for part in (_stringify_value(item) for item in value) if part.strip()
        )
    return str(value).strip()
