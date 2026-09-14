import json
from typing import Dict, List, Optional, Any

SITUATION_SYSTEM_PROMPT = """Classify the user's described situation into exactly one
situation_type from:
- pre_signing_review
- active_dispute
- termination
- renewal_negotiation
- general_curiosity

Assign urgency (low/medium/high) and up to 4 relevant_categories from the clause category list:
(rent_fees, term_renewal, termination_penalties, repairs_habitability, access_privacy, deposit, restrictions, other).
Do not give advice here — classification only.

Output strictly in JSON matching this schema:
{
  "situation_type": "pre_signing_review" | "active_dispute" | "termination" | "renewal_negotiation" | "general_curiosity",
  "urgency": "low" | "medium" | "high",
  "relevant_categories": [string]
}
"""

ACTION_PLAN_SYSTEM_PROMPT = """Using the situation classification and the relevant findings
below, produce an ordered list of concrete next steps a tenant could
take. Cite the document wherever a step references a specific clause.
Never promise a legal outcome. If the situation is active_dispute or
urgency is high, the final step must recommend seeking professional
help and explain why.
Never include fabricated statute numbers, case names, or legal citations of any kind (e.g. "§", "Civ. Code", "v.").

Output strictly in JSON matching this schema:
{
  "steps": [
    {
      "order": int,
      "action": string,
      "rationale": string,
      "citation": {
        "page": int,
        "clause_id": string,
        "quote": string (verbatim excerpt from the document)
      } or null
    }
  ]
}
"""

LAWYER_QUESTION_SYSTEM_PROMPT = """Generate specific, non-generic questions a tenant should ask a
lawyer or tenant-rights clinic, grouped by topic, based on the findings
and situation below. Never include statute numbers, case names, or any
citation-shaped legal authority (e.g. "§", "Civ. Code", "v.") — you do
not have a verified source for those. Prioritize questions tied to
high-severity findings.

Output strictly in JSON matching this schema:
{
  "questions": [
    {
      "topic": string,
      "question": string,
      "priority": "low" | "medium" | "high",
      "source_finding_id": string or null
    }
  ]
}
"""


def format_situation_prompt(context_text: str) -> str:
    return f"SITUATION: {context_text}"


def format_action_plan_prompt(situation: Dict[str, Any], findings: List[Dict[str, Any]]) -> str:
    return f"SITUATION: {json.dumps(situation, indent=2)}\n\nRELEVANT FINDINGS: {json.dumps(findings, indent=2)}"


def format_lawyer_questions_prompt(findings: List[Dict[str, Any]], situation: Optional[Dict[str, Any]] = None) -> str:
    sit_str = json.dumps(situation, indent=2) if situation else "Not specified"
    return f"FINDINGS: {json.dumps(findings, indent=2)}\n\nSITUATION: {sit_str}"
