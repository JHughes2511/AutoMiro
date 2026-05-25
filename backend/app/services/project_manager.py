"""
ProjectManager — runs and manages a full AutoMiro research project.

Coordinates: Intake → Domain Agents + Challengers → Synthesis → Output
Handles project state persistence and live status streaming.
"""

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from ..config import Config
from ..movement.orchestrator import Movement
from ..agents.intake import IntakeAgent
from ..agents.domain import DomainAgent
from ..agents.challenger import ChallengerAgent
from ..agents.synthesis import SynthesisAgent
from ..memory.graph import MemoryGraph
from ..utils.logger import get_logger

logger = get_logger("services.project_manager")


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    CLARIFYING = "clarifying"
    RUNNING = "running"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Project:
    project_id: str
    name: str
    brief: str
    status: ProjectStatus = ProjectStatus.DRAFT
    scope: dict = field(default_factory=dict)
    clarifications: dict = field(default_factory=dict)
    clarifying_questions: list = field(default_factory=list)
    agent_states: dict = field(default_factory=dict)
    synthesis_result: dict = field(default_factory=dict)
    morning_report: str = ""
    round_number: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "brief": self.brief,
            "status": self.status.value,
            "scope": self.scope,
            "clarifications": self.clarifications,
            "clarifying_questions": self.clarifying_questions,
            "agent_states": self.agent_states,
            "synthesis_result": self.synthesis_result,
            "morning_report": self.morning_report,
            "round_number": self.round_number,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }


class ProjectManager:
    def __init__(self):
        self.movement = Movement()
        self.memory = MemoryGraph()
        self._projects: dict[str, Project] = {}
        self._load_persisted_projects()

    def create_project(self, name: str, brief: str) -> Project:
        project_id = str(uuid.uuid4())[:8]
        project = Project(project_id=project_id, name=name, brief=brief)
        self._projects[project_id] = project
        self._persist(project)
        logger.info(f"[PM] Created project {project_id}: {name}")
        return project

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list_projects(self) -> list[dict]:
        return [p.to_dict() for p in self._projects.values()]

    def generate_clarifying_questions(self, project_id: str) -> list[dict]:
        project = self._get_or_raise(project_id)
        project.status = ProjectStatus.CLARIFYING
        intake = IntakeAgent(self.movement)
        questions = intake.generate_clarifying_questions(project.brief)
        project.clarifying_questions = questions
        project.updated_at = time.time()
        self._persist(project)
        return questions

    def submit_clarifications(self, project_id: str, clarifications: dict):
        """User answers the clarifying questions. Structures the scope."""
        project = self._get_or_raise(project_id)
        project.clarifications = clarifications
        intake = IntakeAgent(self.movement)
        scope = intake.structure_scope(project.brief, clarifications)
        project.scope = scope
        project.updated_at = time.time()
        self._persist(project)
        logger.info(f"[PM] Scope structured for {project_id}: {len(scope.get('domains_needed', []))} domains")
        return scope

    def add_to_brief(self, project_id: str, additional_input: str):
        """Continuous feeding — user adds more context mid-project."""
        project = self._get_or_raise(project_id)
        intake = IntakeAgent(self.movement)
        updated_scope = intake.add_to_scope(project.scope, additional_input)
        project.scope = updated_scope
        project.brief += f"\n\n[Added context] {additional_input}"
        project.updated_at = time.time()
        self._persist(project)
        return updated_scope

    def start_research(self, project_id: str, on_update: Callable | None = None) -> str:
        """
        Kicks off the full research run in a background thread.
        on_update(project_dict) called after each agent completes.
        Returns thread id.
        """
        project = self._get_or_raise(project_id)
        if not project.scope:
            raise ValueError("Scope must be structured before starting research")

        thread = threading.Thread(
            target=self._run_research,
            args=(project_id, on_update),
            daemon=True,
        )
        thread.start()
        return thread.name

    def _run_research(self, project_id: str, on_update: Callable | None = None):
        project = self._get_or_raise(project_id)
        project.status = ProjectStatus.RUNNING
        project.updated_at = time.time()
        self._persist(project)

        try:
            scope = project.scope
            domains = scope.get("domains_needed", ["finance", "technology", "risk"])

            logger.info(f"[PM] Starting swarm for {project_id} — {len(domains)} domains")

            domain_agents: dict[str, DomainAgent] = {}
            challenger_agents: dict[str, ChallengerAgent] = {}

            for domain in domains:
                domain_agents[domain] = DomainAgent(domain, project_id, self.movement)
                challenger_agents[domain] = ChallengerAgent(domain, self.movement)

            # Run domain agents — currently sequential to stay within free-tier rate limits
            # Phase 2: parallel with semaphore
            for domain, agent in domain_agents.items():
                logger.info(f"[PM] Running {domain} agent")

                # Inject memory context if available
                memory_ctx = self.memory.get_relevant_context(
                    project_id, scope.get("brief", "")
                )
                if memory_ctx:
                    scope_with_memory = {**scope, "prior_memory": memory_ctx[:1000]}
                else:
                    scope_with_memory = scope

                # Run agent (AutoResearch loop)
                state = agent.run(scope_with_memory)

                # Challenger fires after each domain agent
                if state.current_findings:
                    challenge = challenger_agents[domain].challenge(
                        state.current_findings, scope, state.best_confidence
                    )
                    agent.receive_challenge(challenge)

                    # One more iteration with challenger feedback
                    if state.best_confidence < 0.85:
                        logger.info(f"[PM] {domain} agent running post-challenge iteration")
                        agent.max_iterations = 1
                        agent.run(scope_with_memory)

                # Store agent finding in memory
                self.memory.store_agent_finding(
                    project_id, domain, state.current_findings, state.best_confidence
                )

                project.agent_states[domain] = state.to_dict()
                project.updated_at = time.time()
                self._persist(project)

                if on_update:
                    on_update(project.to_dict())

            # Synthesis phase
            project.status = ProjectStatus.SYNTHESIZING
            self._persist(project)

            logger.info(f"[PM] Starting synthesis for {project_id}")
            synthesis_agent = SynthesisAgent(self.movement)

            domain_results = {
                domain: {
                    "current_findings": agent.state.current_findings,
                    "best_confidence": agent.state.best_confidence,
                }
                for domain, agent in domain_agents.items()
            }

            synthesis_result = synthesis_agent.synthesize(domain_results, scope)
            morning_report = synthesis_agent.generate_morning_report(synthesis_result, scope)

            project.synthesis_result = synthesis_result
            project.morning_report = morning_report
            project.status = ProjectStatus.COMPLETE
            project.updated_at = time.time()
            self._persist(project)

            # Store full project in memory for future rounds
            self.memory.store_project_research(project_id, scope, synthesis_result)

            logger.info(f"[PM] Project {project_id} complete")

            if on_update:
                on_update(project.to_dict())

        except Exception as e:
            logger.error(f"[PM] Project {project_id} failed: {e}", exc_info=True)
            project.status = ProjectStatus.FAILED
            project.error = str(e)
            project.updated_at = time.time()
            self._persist(project)
            if on_update:
                on_update(project.to_dict())

    def chat_with_agent(self, project_id: str, domain: str, user_message: str) -> str:
        """User talks directly to a specific domain agent for deeper dialogue."""
        project = self._get_or_raise(project_id)
        agent_state = project.agent_states.get(domain, {})
        findings = agent_state.get("current_findings", "No findings yet.")
        confidence = agent_state.get("best_confidence", 0.0)
        breakdown = agent_state.get("confidence_breakdown", {})
        scope = project.scope
        brief = project.brief
        clarifications = project.clarifications

        from ..movement.orchestrator import TaskContext, TaskComplexity
        from ..agents.domain import DOMAIN_CONFIGS

        cfg = DOMAIN_CONFIGS.get(domain.lower(), {"system": f"You are an expert {domain} analyst.", "focus": domain})

        system = f"""{cfg['system']}

ORIGINAL RESEARCH BRIEF:
{brief}

RESEARCH SCOPE:
Objective: {scope.get('objective', '')}
Layers: {', '.join(scope.get('layers', []))}
Time horizon: {scope.get('time_horizon', '7 years')}
Success metric: {scope.get('success_metric', '5x return')}
Constraints: {', '.join(scope.get('constraints', []))}
Key questions: {json.dumps(scope.get('key_questions', []))}

USER CLARIFICATIONS:
{json.dumps(clarifications, indent=2)}

YOUR COMPLETED RESEARCH FINDINGS (confidence: {confidence:.0%}):
{findings}

CONFIDENCE BREAKDOWN:
- Evidence Quality: {breakdown.get('evidence_quality', 0)}%
- Source Diversity: {breakdown.get('source_diversity', 0)}%
- Challenge Resolved: {breakdown.get('challenge_resolved', 0)}%
- Risk Coverage: {breakdown.get('risk_coverage', 0)}%

You are in a live conversation with the user about your research. Be direct, specific,
and honest. Reference specific tickers, numbers, and data points from your findings.
If the user provides new information that changes your analysis, say so explicitly.
If asked what would change your view, give concrete thresholds, not vague hedges."""

        task = TaskContext(
            task_id=f"agent-chat-{domain}",
            complexity=TaskComplexity.MID,
            system_prompt=system,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=2048,
        )
        return self.movement.run_task(task)

    def _get_or_raise(self, project_id: str) -> Project:
        project = self._projects.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project

    def _persist(self, project: Project):
        path = os.path.join(Config.PROJECTS_DIR, f"{project.project_id}.json")
        with open(path, "w") as f:
            json.dump(project.to_dict(), f, indent=2)

    def _load_persisted_projects(self):
        if not os.path.exists(Config.PROJECTS_DIR):
            return
        for fname in os.listdir(Config.PROJECTS_DIR):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(Config.PROJECTS_DIR, fname)) as f:
                    data = json.load(f)
                project = Project(
                    project_id=data["project_id"],
                    name=data["name"],
                    brief=data["brief"],
                    status=ProjectStatus(data.get("status", "draft")),
                    scope=data.get("scope", {}),
                    clarifications=data.get("clarifications", {}),
                    clarifying_questions=data.get("clarifying_questions", []),
                    agent_states=data.get("agent_states", {}),
                    synthesis_result=data.get("synthesis_result", {}),
                    morning_report=data.get("morning_report", ""),
                    round_number=data.get("round_number", 1),
                    created_at=data.get("created_at", time.time()),
                    updated_at=data.get("updated_at", time.time()),
                )
                self._projects[project.project_id] = project
            except Exception as e:
                logger.warning(f"[PM] Failed to load {fname}: {e}")

        logger.info(f"[PM] Loaded {len(self._projects)} persisted projects")
