"""
SynthesisAgent — reads all domain outputs and produces the final vision.

Finds convergences (high confidence outcomes), maps divergences (tensions
between domains), scores plausibility unbiasedly by evidence quality +
domain frequency, and ranks outcomes.
"""

import json
from ..movement.orchestrator import Movement, TaskComplexity, TaskContext
from ..utils.logger import get_logger

logger = get_logger("agents.synthesis")

SYNTHESIS_SYSTEM = """You are the AutoMiro Synthesis Agent.
You read research from multiple domain experts and produce an unbiased,
evidence-driven synthesis. You find the most plausible outcomes based on
where multiple domains converge — not on any single domain's authority.

You think in probabilities, not certainties. You surface tensions and resolve
them with evidence. Your output is the basis for the user's final decision."""


class SynthesisAgent:
    def __init__(self, movement: Movement):
        self.movement = movement

    def synthesize(self, domain_results: dict, scope: dict) -> dict:
        """
        Core synthesis. Takes all domain agent results and produces:
        - ranked outcomes by plausibility
        - convergence map
        - divergence/tension points
        - top picks per layer
        - morning report summary
        """
        # Build the domain findings context
        findings_context = self._format_domain_findings(domain_results)

        # Stage 1 (Fast barrel): Extract key claims per domain
        claims = self._extract_claims(findings_context, scope)

        # Stage 2 (Mid barrel): Find convergences and divergences
        convergence_map = self._map_convergences(claims, scope)

        # Stage 3 (Heavy barrel): Final vision and ranked outcomes
        final_vision = self._build_final_vision(convergence_map, findings_context, scope)

        return {
            "claims_by_domain": claims,
            "convergence_map": convergence_map,
            "final_vision": final_vision,
            "domain_confidences": {
                domain: result.get("best_confidence", 0.0)
                for domain, result in domain_results.items()
            },
        }

    def _format_domain_findings(self, domain_results: dict) -> str:
        parts = []
        for domain, result in domain_results.items():
            findings = result.get("current_findings", "No findings.")
            confidence = result.get("best_confidence", 0.0)
            parts.append(
                f"=== {domain.upper()} (confidence: {confidence:.0%}) ===\n{findings}\n"
            )
        return "\n".join(parts)

    def _extract_claims(self, findings_context: str, scope: dict) -> str:
        prompt = f"""From these domain research findings, extract the key claims each domain is making.

{findings_context}

For each domain, list:
- Their top 3 claims (specific, factual assertions)
- Their top 2-3 ticker/company recommendations with brief justification
- Their primary concern or risk flag

Keep it structured and scannable."""

        task = TaskContext(
            task_id="synthesis-extract-claims",
            complexity=TaskComplexity.FAST,
            system_prompt=SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        return self.movement.run_task(task)

    def _map_convergences(self, claims: str, scope: dict) -> str:
        prompt = f"""Analyze these domain claims and map convergences and divergences.

{claims}

Produce:

CONVERGENCES (multiple domains agree):
- List each point where 2+ domains reach similar conclusions
- Note which domains converge on each point
- Assign a plausibility score (0-100) based on evidence quality + domain count

DIVERGENCES (domains conflict or pull different directions):
- List each tension point
- Explain why domains disagree
- Assess which perspective has stronger evidence

CONSENSUS TICKERS:
- Which specific tickers appear across multiple domains as strong candidates?
- List with how many domains flagged them and why

MOST PLAUSIBLE OUTCOME:
- Based purely on convergence frequency and evidence quality, what is the most likely outcome?"""

        task = TaskContext(
            task_id="synthesis-convergence-map",
            complexity=TaskComplexity.MID,
            system_prompt=SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            wound_context=self.movement.wind(claims),
        )
        return self.movement.run_task(task)

    def _build_final_vision(self, convergence_map: str, full_context: str, scope: dict) -> dict:
        layers = scope.get("layers", [])
        time_horizon = scope.get("time_horizon", "7 years")
        success_metric = scope.get("success_metric", "5x return")

        prompt = f"""You have the full research context and convergence analysis. Build the final vision.

CONVERGENCE ANALYSIS:
{convergence_map}

FULL DOMAIN RESEARCH:
{full_context[:4000]}

SCOPE: {scope.get('brief', '')}
SUCCESS METRIC: {success_metric} in {time_horizon}
LAYERS: {', '.join(layers) if layers else 'as identified'}

Produce the Final Vision as JSON:
{{
  "headline": "one sentence summary of the most plausible outcome",
  "overall_confidence": 0.0-1.0,
  "plausibility_ranking": [
    {{
      "outcome": "description",
      "plausibility_score": 0-100,
      "supporting_domains": ["domain1", ...],
      "evidence_strength": "strong|moderate|weak"
    }}
  ],
  "top_picks_by_layer": {{
    "layer_name": [
      {{
        "ticker": "TICKER",
        "name": "Company Name",
        "thesis": "why this ticker meets the {success_metric} in {time_horizon} goal",
        "domain_support": ["which domains flagged this"],
        "confidence": 0.0-1.0,
        "key_risk": "primary risk to thesis"
      }}
    ]
  }},
  "key_convergences": ["finding that multiple domains agree on"],
  "key_tensions": ["unresolved conflict between domains"],
  "assumptions_to_monitor": ["what to watch that could invalidate this vision"],
  "next_research_round": ["what gaps remain that a follow-up round should address"],
  "morning_report": "3-5 paragraph executive summary written directly to the user"
}}

Return only the JSON object."""

        task = TaskContext(
            task_id="synthesis-final-vision",
            complexity=TaskComplexity.HEAVY,
            system_prompt=SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            wound_context=self.movement.wind(convergence_map, {"full_context_length": len(full_context)}),
        )
        raw = self.movement.run_task(task)

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except Exception as e:
            logger.warning(f"Failed to parse final vision JSON: {e}")
            return {"morning_report": raw, "error": "Could not parse structured output"}

    def generate_morning_report(self, synthesis_result: dict, scope: dict) -> str:
        """Generate a clean, standalone morning report from synthesis results."""
        vision = synthesis_result.get("final_vision", {})
        if isinstance(vision, dict) and "morning_report" in vision:
            base_report = vision["morning_report"]
        else:
            base_report = str(vision)

        prompt = f"""Format this research synthesis into a clean morning report.

Raw synthesis:
{base_report}

Scope: {scope.get('brief', '')}

Format as:
# AutoMiro Research Report
**[Date] | [Scope headline]**

## Bottom Line Up Front
[2-3 sentences: what to do and why]

## Top Picks by Layer
[Organized by the technology layers, 3-5 tickers per layer with thesis]

## Key Convergences
[What multiple research domains agreed on]

## Key Tensions to Watch
[Where domains disagreed — monitor these]

## Confidence Assessment
[Overall confidence and what would change it]

## Next Steps
[What to research in the next round]

Write in plain, direct language. No hedging. No filler."""

        task = TaskContext(
            task_id="synthesis-morning-report",
            complexity=TaskComplexity.HEAVY,
            system_prompt=SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
        )
        return self.movement.run_task(task)
