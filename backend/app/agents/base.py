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
from typing import Any

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
class ResearchIteration:
    iteration: int
    hypothesis: str
    evidence: list[str]
    confidence: float       # 0.0 – 1.0
    approach: str
    kept: bool
    reasoning: str


@dataclass
class AgentState:
    agent_id: str
    domain: str
    project_id: str
    status: AgentStatus = AgentStatus.IDLE
    iterations: list[ResearchIteration] = field(default_factory=list)
    best_confidence: float = 0.0
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
            "current_findings": self.current_findings,
            "iterations_count": len(self.iterations),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class BaseAgent(ABC):
    """
    Abstract base for all AutoMiro agents.
    Subclasses implement `research_step` — the core domain logic.
    The AutoResearch loop runs here.
    """

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
        Returns: {evidence: [...], confidence: float, findings: str, approach: str}
        """

    @abstractmethod
    def form_initial_hypothesis(self, scope: dict) -> str:
        """Produce the first hypothesis given the brief scope."""

    def run(self, scope: dict) -> AgentState:
        """
        AutoResearch loop. Runs until confidence plateaus or iteration limit hit.
        """
        self.state.status = AgentStatus.RESEARCHING
        logger.info(f"[{self.domain}:{self.agent_id}] Starting research loop")

        hypothesis = self.form_initial_hypothesis(scope)
        best_findings = ""
        best_confidence = 0.0

        for i in range(self.max_iterations):
            self.state.status = AgentStatus.ITERATING
            logger.info(f"[{self.domain}:{self.agent_id}] Iteration {i+1}/{self.max_iterations}")

            result = self.research_step(scope, hypothesis, best_findings)

            confidence = result.get("confidence", 0.0)
            findings = result.get("findings", "")
            approach = result.get("approach", "")
            evidence = result.get("evidence", [])

            kept = confidence > best_confidence
            iteration = ResearchIteration(
                iteration=i + 1,
                hypothesis=hypothesis,
                evidence=evidence,
                confidence=confidence,
                approach=approach,
                kept=kept,
                reasoning=result.get("reasoning", ""),
            )
            self.state.iterations.append(iteration)

            if kept:
                best_confidence = confidence
                best_findings = findings
                self.state.best_confidence = best_confidence
                self.state.current_findings = best_findings
                logger.info(f"[{self.domain}:{self.agent_id}] ✓ Kept — confidence {confidence:.2f}")
            else:
                logger.info(f"[{self.domain}:{self.agent_id}] ✗ Discarded — confidence {confidence:.2f} ≤ {best_confidence:.2f}")

            # Form next hypothesis from challenger feedback + current findings
            hypothesis = self._evolve_hypothesis(scope, best_findings, self.state.challenger_feedback)

            # Early exit if confidence is very high
            if best_confidence >= 0.88:
                logger.info(f"[{self.domain}:{self.agent_id}] High confidence reached, stopping early")
                break

        self.state.status = AgentStatus.COMPLETE
        self.state.updated_at = time.time()
        logger.info(f"[{self.domain}:{self.agent_id}] Complete — final confidence {self.state.best_confidence:.2f}")
        return self.state

    def receive_challenge(self, feedback: str):
        """Challenger agent injects feedback into this agent's next iteration."""
        self.state.challenger_feedback = feedback
        self.state.status = AgentStatus.CHALLENGED

    def _evolve_hypothesis(self, scope: dict, current_findings: str, challenger_feedback: str) -> str:
        """Use the mid model to evolve the hypothesis based on findings + challenge."""
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
