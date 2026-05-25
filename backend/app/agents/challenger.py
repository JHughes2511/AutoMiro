"""
ChallengerAgent — keeps every domain agent on its toes.

Assigned to a specific domain agent. Reads its findings and produces
adversarial feedback: challenges assumptions, flags evidence gaps,
and proposes alternative interpretations.
"""

import json
from ..movement.orchestrator import Movement, TaskComplexity, TaskContext
from ..utils.logger import get_logger

logger = get_logger("agents.challenger")

CHALLENGER_SYSTEM = """You are a Devil's Advocate research challenger.
Your job is NOT to be negative for its own sake — it's to make the research
sharper by finding the weakest points, hidden assumptions, and missing evidence.
You ask the questions the domain agent didn't ask itself.
A great challenge is specific, cites what's missing, and proposes a better angle."""


class ChallengerAgent:
    def __init__(self, target_domain: str, movement: Movement):
        self.target_domain = target_domain
        self.movement = movement

    def challenge(self, domain_findings: str, scope: dict, confidence: float) -> str:
        """
        Read domain agent findings and produce targeted adversarial feedback.
        Returns challenge string injected back into the domain agent's next iteration.
        """
        prompt = f"""You are challenging a {self.target_domain} research agent.

Their findings (confidence: {confidence:.0%}):
{domain_findings[:3000]}

Research scope:
{json.dumps(scope, indent=2)}

Produce a sharp challenge covering:
1. ASSUMPTION GAPS: What assumptions did they make that aren't proven?
2. EVIDENCE GAPS: What data did they not look for that could change the conclusion?
3. COUNTER-SCENARIO: Describe the most plausible scenario where their conclusion is wrong
4. MISSING ANGLE: What {self.target_domain}-specific factor did they overlook?
5. SHARPENING QUESTION: The one question they must answer to increase confidence

Be specific. Reference their actual claims. Don't be generic.
Keep it under 400 words — focus on the 2-3 most important challenges."""

        task = TaskContext(
            task_id=f"challenger-{self.target_domain}",
            complexity=TaskComplexity.MID,
            system_prompt=CHALLENGER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
        )
        feedback = self.movement.run_task(task)
        logger.info(f"[Challenger→{self.target_domain}] Challenge generated")
        return feedback
