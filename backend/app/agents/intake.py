"""
IntakeAgent — the front door of AutoMiro.

Reads the user's brief, asks targeted clarifying questions,
structures the scope into layers the domain agents can work from,
and auto-detects which domains need to be activated.
"""

import json
from ..movement.orchestrator import Movement, TaskComplexity, TaskContext
from ..utils.logger import get_logger

logger = get_logger("agents.intake")

ALL_DOMAINS = [
    "finance", "technology", "geopolitical", "market_sentiment",
    "risk", "supply_chain", "regulatory", "competitive",
]

INTAKE_SYSTEM = """You are the AutoMiro intake agent. Your job is to:
1. Understand the user's brief deeply
2. Ask sharp clarifying questions that will meaningfully shape the research
3. Identify the research layers and structure the scope
4. Determine which expert domains should be activated

You think in layers — like an infrastructure stack. You identify what the user
said, what they implied, and critically, what they haven't considered yet."""


class IntakeAgent:
    def __init__(self, movement: Movement):
        self.movement = movement

    def generate_clarifying_questions(self, brief: str) -> list[dict]:
        """
        Generate 3-6 targeted questions before agents swarm.
        Returns list of {question, category, why_it_matters}
        """
        prompt = f"""A user submitted this research brief:

"{brief}"

Generate 3 to 6 clarifying questions that will materially improve the research quality.

Rules:
- Ask about things they haven't mentioned but that WILL affect the outcome
- Don't ask about things clearly stated in the brief
- Each question should unlock a different dimension of the research
- Include at least one question about time horizon, risk tolerance, or constraints
- Include at least one question about what they already know or have access to
- Flag any assumptions baked into the brief that could be wrong

Return a JSON array:
[
  {{
    "question": "...",
    "category": "one of: scope | constraints | context | risk | assumptions | data",
    "why_it_matters": "one sentence on how the answer changes the research direction"
  }}
]

Return only the JSON array, no other text."""

        task = TaskContext(
            task_id="intake-clarifying-questions",
            complexity=TaskComplexity.MID,
            system_prompt=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        raw = self.movement.run_task(task)

        try:
            start = raw.find("[")
            end = raw.rfind("]") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("Failed to parse clarifying questions as JSON, returning raw")
            return [{"question": raw, "category": "scope", "why_it_matters": "Context"}]

    def structure_scope(self, brief: str, clarifications: dict) -> dict:
        """
        After clarifications are answered, structure the full research scope.
        Returns the scope dict that all domain agents will receive.
        """
        clarification_str = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in clarifications.items()
        ) if clarifications else "No clarifications provided."

        prompt = f"""Original brief:
"{brief}"

Clarifications received:
{clarification_str}

Structure this into a research scope. Return JSON:
{{
  "brief": "refined one-paragraph version of what we're actually researching",
  "objective": "the single most important outcome the user wants",
  "layers": ["layer1", "layer2", ...],
  "time_horizon": "e.g. 7 years",
  "success_metric": "e.g. 5x return per ticker",
  "constraints": ["constraint1", ...],
  "suggested_tickers": ["TICKER1", ...],
  "domains_needed": ["finance", "technology", ...],
  "key_questions": ["question the research must answer", ...],
  "assumptions_to_test": ["assumption1", ...]
}}

For domains_needed, choose from: {json.dumps(ALL_DOMAINS)}
Include every domain that's genuinely relevant to the scope.
For suggested_tickers: include any the user mentioned + any obvious candidates you know.

Return only the JSON object."""

        task = TaskContext(
            task_id="intake-structure-scope",
            complexity=TaskComplexity.MID,
            system_prompt=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        raw = self.movement.run_task(task)

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            scope = json.loads(raw[start:end])
            # Ensure domains_needed only contains known domains
            scope["domains_needed"] = [
                d for d in scope.get("domains_needed", ALL_DOMAINS)
                if d in ALL_DOMAINS
            ]
            return scope
        except Exception as e:
            logger.warning(f"Failed to parse scope JSON: {e}")
            return {
                "brief": brief,
                "objective": brief,
                "layers": [],
                "domains_needed": ALL_DOMAINS,
                "clarifications": clarifications,
            }

    def add_to_scope(self, existing_scope: dict, new_input: str) -> dict:
        """
        Continuous feeding — user adds more context to an existing scope.
        Merges new input with existing scope without discarding prior context.
        """
        prompt = f"""Existing research scope:
{json.dumps(existing_scope, indent=2)}

New information from the user:
"{new_input}"

Update the scope by incorporating the new information.
Preserve everything already in the scope.
Add/update only what the new input changes or adds.
Return the complete updated scope JSON in the same format."""

        task = TaskContext(
            task_id="intake-add-to-scope",
            complexity=TaskComplexity.MID,
            system_prompt=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        raw = self.movement.run_task(task)

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            logger.warning("Failed to parse updated scope, returning existing")
            return existing_scope
