"""
BaseAgent — every agent in AutoMiro inherits from this.

Implements the AutoResearch loop:
  form hypothesis → gather evidence → score confidence
  → if improved: keep approach → else: try new angle → repeat
"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from ..movement.orchestrator import Movement, TaskComplexity, TaskContext
from ..utils.logger import get_logger

logger = get_logger("agents.base")


class AgentStatus(str, Enum):
    IDLE = "idle"
    RESEARCHING = "researching"
    ITERATING = "iterating"
    CHALLENGED = "challenged"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ConfidenceBreakdown:
    evidence_quality: float = 0.0       # concrete data points vs. pure reasoning
    source_diversity: float = 0.0       # variety of independent sources used
    challenge_resolved: float = 0.0     # how well challenger feedback was addressed
    risk_coverage: float = 0.0          # whether key risks were identified and assessed
    overall: float = 0.0                # weighted composite

    def to_dict(self) -> dict:
        return {
            "evidence_quality": round(self.evidence_quality * 100),
            "source_diversity": round(self.source_diversity * 100),
            "challenge_resolved": round(self.challenge_resolved * 100),
            "risk_coverage": round(self.risk_coverage * 100),
            "overall": round(self.overall * 100),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConfidenceBreakdown":
        def pct(v):
            if v is None:
                return 0.0
            return float(v) / 100 if float(v) > 1 else float(v)
        return cls(
            evidence_quality=pct(d.get("evidence_quality", 0)),
            source_diversity=pct(d.get("source_diversity", 0)),
            challenge_resolved=pct(d.get("challenge_resolved", 0)),
            risk_coverage=pct(d.get("risk_coverage", 0)),
            overall=pct(d.get("overall", 0)),
        )

    @staticmethod
    def compute_overall(eq: float, sd: float, cr: float, rc: float) -> float:
        return round(eq * 0.35 + sd * 0.20 + cr * 0.25 + rc * 0.20, 3)


@dataclass
class ResearchIteration:
    iteration: int
    hypothesis: str
    evidence: list[str]
    confidence: float
    confidence_breakdown: ConfidenceBreakdown = field(default_factory=ConfidenceBreakdown)
    approach: str = ""
    kept: bool = False
    reasoning: str = ""


@dataclass
class AgentState:
    agent_id: str
    domain: str
    project_id: str
    status: AgentStatus = AgentStatus.IDLE
    iterations: list[ResearchIteration] = field(default_factory=list)
    best_confidence: float = 0.0
    best_confidence_breakdown: ConfidenceBreakdown = field(default_factory=ConfidenceBreakdown)
    current_findings: str = ""
    challenger_feedback: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "project_id": self.project_id,
            "status": self.status.value,
            "best_confidence": self.best_confidence,
            "confidence_breakdown": self.best_confidence_breakdown.to_dict(),
            "current_findings": self.current_findings,
            "iterations_count": len(self.iterations),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class BaseAgent(ABC):
    def __init__(self, domain: str, project_id: str, movement: Movement):
        self.agent_id = str(uuid.uuid4())[:8]
        self.domain = domain
        self.project_id = project_id
        self.movement = movement
        self.state = AgentState(
            agent_id=self.agent_id,
            domain=domain,
            project_id=project_id,
        )
        self.max_iterations = 5

    @abstractmethod
    def research_step(self, scope: dict, hypothesis: str, previous_findings: str) -> dict:
        """
        One iteration of domain research.
        Returns: {evidence, confidence_breakdown: dict, findings, approach, reasoning}
        """

    @abstractmethod
    def form_initial_hypothesis(self, scope: dict) -> str:
        """Produce the first hypothesis given the brief scope."""

    def run(self, scope: dict) -> AgentState:
        self.state.status = AgentStatus.RESEARCHING
        logger.info(f"[{self.domain}:{self.agent_id}] Starting research loop")

        hypothesis = self.form_initial_hypothesis(scope)
        best_findings = ""
        best_confidence = 0.0

        for i in range(self.max_iterations):
            self.state.status = AgentStatus.ITERATING
            logger.info(f"[{self.domain}:{self.agent_id}] Iteration {i+1}/{self.max_iterations}")

            result = self.research_step(scope, hypothesis, best_findings)

            breakdown_raw = result.get("confidence_breakdown", {})
            breakdown = ConfidenceBreakdown.from_dict(breakdown_raw) if breakdown_raw else ConfidenceBreakdown()

            # Compute overall from components so it's always earned, never defaulted
            if breakdown.overall == 0.0 and any([
                breakdown.evidence_quality, breakdown.source_diversity,
                breakdown.challenge_resolved, breakdown.risk_coverage
            ]):
                breakdown.overall = ConfidenceBreakdown.compute_overall(
                    breakdown.evidence_quality, breakdown.source_diversity,
                    breakdown.challenge_resolved, breakdown.risk_coverage,
                )

            confidence = breakdown.overall or result.get("confidence", 0.0)
            findings = result.get("findings", "")
            approach = result.get("approach", "")
            evidence = result.get("evidence", [])

            kept = confidence > best_confidence
            iteration = ResearchIteration(
                iteration=i + 1,
                hypothesis=hypothesis,
                evidence=evidence,
                confidence=confidence,
                confidence_breakdown=breakdown,
                approach=approach,
                kept=kept,
                reasoning=result.get("reasoning", ""),
            )
            self.state.iterations.append(iteration)

            if kept:
                best_confidence = confidence
                best_findings = findings
                self.state.best_confidence = best_confidence
                self.state.best_confidence_breakdown = breakdown
                self.state.current_findings = best_findings
                logger.info(f"[{self.domain}:{self.agent_id}] ✓ Kept — confidence {confidence:.2f}")
            else:
                logger.info(f"[{self.domain}:{self.agent_id}] ✗ Discarded — confidence {confidence:.2f} ≤ {best_confidence:.2f}")

            hypothesis = self._evolve_hypothesis(scope, best_findings, self.state.challenger_feedback)

            if best_confidence >= 0.88:
                logger.info(f"[{self.domain}:{self.agent_id}] High confidence reached, stopping early")
                break

        self.state.status = AgentStatus.COMPLETE
        self.state.updated_at = time.time()
        logger.info(f"[{self.domain}:{self.agent_id}] Complete — overall confidence {self.state.best_confidence:.2f}")
        return self.state

    def receive_challenge(self, feedback: str):
        self.state.challenger_feedback = feedback
        self.state.status = AgentStatus.CHALLENGED

    def _evolve_hypothesis(self, scope: dict, current_findings: str, challenger_feedback: str) -> str:
        if not current_findings:
            return self.form_initial_hypothesis(scope)

        prompt = f"""You are a {self.domain} research agent evolving your hypothesis.

Current findings summary:
{current_findings[:1000]}

Challenger feedback:
{challenger_feedback or "None yet"}

Scope:
{json.dumps(scope, indent=2)}

Generate a sharper, more specific hypothesis for the next research iteration.
Focus on what the challenger questioned or what evidence gaps remain.
Return only the hypothesis statement, 1-3 sentences."""

        task = TaskContext(
            task_id=f"{self.agent_id}-evolve-hypothesis",
            complexity=TaskComplexity.MID,
            system_prompt=f"You are an expert {self.domain} researcher.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return self.movement.run_task(task)

    def get_status(self) -> dict:
        return self.state.to_dict()
