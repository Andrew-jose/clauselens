import re
import json
import logging
from typing import Any, Dict, List, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

# Regex pattern rejecting fabricated statute citations or case names (§7.7)
FABRICATED_LEGAL_CITATION_PATTERN = re.compile(
    r'(?:§+\s*[0-9]+|(?:Section|Sec\.)\s+[0-9]+(?:\s+of\s+the\s+[A-Za-z\s]+Act(?:\s+[0-9]{4})?)?|(?:[A-Z][a-z]+\.?\s+)+(?:Code|Stat|Ann\.|Rev\.|Reg\.|Act(?:\s+[0-9]{4})?)|(?:[A-Z][a-z]+)\s+v\.\s+(?:[A-Z][a-z]+))',
    re.IGNORECASE
)

SELF_CHECK_SYSTEM_PROMPT = """You are an independent citation consistency verifier.
Your job is to check if EVERY factual claim/sentence in the proposed ANSWER is strictly supported by at least one of the PROVIDED CITATION QUOTES.
Never allow general assumptions or outside knowledge.

Output strictly in JSON:
{
  "all_sentences_grounded": boolean,
  "unsupported_sentences": [string],
  "reason": string
}
"""


def strip_fabricated_citations(text: str) -> str:
    """
    Remove or replace prohibited statute/case citations with neutral phrasing.
    Enforces the non-negotiable rule against hallucinated legal authorities.
    """
    if not text:
        return text

    def replace_citation(match):
        return "[statutory reference withheld; verify with local counsel]"

    return FABRICATED_LEGAL_CITATION_PATTERN.sub(replace_citation, text)


def run_self_check_verifier(
    answer: str,
    citations: List[Dict[str, Any]],
    retrieved_chunks_text: str,
) -> Tuple[bool, List[str]]:
    """
    Second-pass self-check verifier (§7.6).
    Checks that every sentence in draft answer has a verified citation anchor.
    Returns (is_grounded, unsupported_sentences).
    """
    if not citations:
        # If there are zero citations, an answer cannot be grounded
        sentences = [s.strip() for s in re.split(r'[\.\\?\!]+', answer) if len(s.strip()) > 10]
        return False, sentences

    # If Gemini API key is available, execute the fast Flash self-check
    if settings.has_gemini_key:
        try:
            from app.services.gemini_client import _ensure_genai_configured
            _ensure_genai_configured()
            import google.generativeai as genai
            model = genai.GenerativeModel(
                settings.GEMINI_FLASH_MODEL,
                generation_config={"response_mime_type": "application/json"},
            )

            quotes_text = "\n".join([f"- \"{c.get('quote', '')}\"" for c in citations])
            user_prompt = f"""PROPOSED ANSWER:
{answer}

PROVIDED CITATIONS:
{quotes_text}

Verify if every sentence in the proposed answer is directly anchored to the provided citations.
"""
            response = model.generate_content(
                [{"role": "user", "parts": [f"{SELF_CHECK_SYSTEM_PROMPT}\n\n{user_prompt}"]}],
                request_options={"timeout": 6},
            )
            result_json = json.loads(response.text)
            is_grounded = bool(result_json.get("all_sentences_grounded", False))
            unsupported = result_json.get("unsupported_sentences", [])
            return is_grounded, unsupported
        except Exception as e:
            logger.warning(f"Flash self-check call failed: {e}. Falling back to heuristic sentence anchor check.")

    # Heuristic fallback verifier: check word/concept overlap between answer sentences and quotes
    sentences = [s.strip() for s in re.split(r'[\.\?\!]+', answer) if len(s.strip()) > 10]
    all_quotes_combined = " ".join([c.get("quote", "").lower() for c in citations])
    all_chunks_combined = retrieved_chunks_text.lower()

    unsupported = []
    for sentence in sentences:
        s_words = [w.lower() for w in re.findall(r'\b\w{4,}\b', sentence)]
        if not s_words:
            continue
        # Count matching meaningful words in quotes or retrieved chunks
        matches = sum(1 for w in s_words if w in all_chunks_combined)
        overlap_pct = matches / len(s_words)

        if overlap_pct < 0.40:
            unsupported.append(sentence)

    is_grounded = len(unsupported) == 0
    return is_grounded, unsupported
