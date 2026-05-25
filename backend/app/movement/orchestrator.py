"""
The Movement — central orchestrator for AutoMiro.

Like a duometre chronograph: two barrels (fast/heavy models) drawing from the
same mainspring (API budget), synchronized by a single escapement (this class).
Complications (domain agents) add depth without disrupting the base movement.
"""

import time
import threading
from enum import Enum
from typing import Any
from dataclasses import dataclass, field

import anthropic

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger("movement.orchestrator")


class TaskComplexity(str, Enum):
    FAST = "fast"       # data gather, search, drafts → Haiku
    MID = "mid"         # domain analysis, challenger → Sonnet
    HEAVY = "heavy"     # synthesis, final vision, judgment → Opus


@dataclass
class TaskContext:
    task_id: str
    complexity: TaskComplexity
    system_prompt: str
    messages: list
    tools: list = field(default_factory=list)
    max_tokens: int = 4096
    wound_context: dict = field(default_factory=dict)   # pre-loaded context from previous barrel


class Movement:
    """
    The central regulator. Routes tasks to the right model barrel,
    manages context winding between barrels, and keeps load balanced
    so no agent starves another.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self._lock = threading.Lock()
        self._active_tasks: dict[str, bool] = {}

        self._model_map = {
            TaskComplexity.FAST: Config.MODEL_FAST,
            TaskComplexity.MID: Config.MODEL_MID,
            TaskComplexity.HEAVY: Config.MODEL_HEAVY,
        }

    def _select_complexity(self, task_type: str, context_size: int) -> TaskComplexity:
        """
        Self-selects complexity level based on task type and accumulated context.
        Large context + synthesis tasks always go heavy.
        """
        synthesis_keywords = {"synthesize", "judge", "final", "vision", "plausibility", "resolve"}
        analysis_keywords = {"analyze", "challenge", "evaluate", "assess", "compare", "domain"}

        task_lower = task_type.lower()

        if any(k in task_lower for k in synthesis_keywords) or context_size > 6000:
            return TaskComplexity.HEAVY
        if any(k in task_lower for k in analysis_keywords):
            return TaskComplexity.MID
        return TaskComplexity.FAST

    def wind(self, fast_result: str, additional_context: dict | None = None) -> dict:
        """
        Winding mechanism: packages fast-barrel output as pre-loaded context
        for the heavy barrel so it fires instantly without cold start.
        """
        wound = {"prior_research": fast_result}
        if additional_context:
            wound.update(additional_context)
        return wound

    def run_task(self, task: TaskContext) -> str:
        """Execute a single task on the appropriate model barrel."""
        model = self._model_map[task.complexity]
        messages = task.messages

        # Inject wound context into first user message if present
        if task.wound_context and messages:
            context_prefix = (
                f"[Pre-loaded context from prior research stage]\n"
                f"{task.wound_context.get('prior_research', '')}\n\n"
                f"[Your task begins here]\n"
            )
            messages = [
                {**messages[0], "content": context_prefix + messages[0]["content"]},
                *messages[1:],
            ]

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": task.max_tokens,
            "system": task.system_prompt,
            "messages": messages,
        }
        if task.tools:
            kwargs["tools"] = task.tools

        logger.info(f"[Movement] {task.task_id} → {task.complexity.value} ({model})")
        start = time.time()

        response = self.client.messages.create(**kwargs)
        elapsed = time.time() - start

        logger.info(f"[Movement] {task.task_id} completed in {elapsed:.1f}s")

        return self._extract_text(response)

    def run_pipeline(self, stages: list[dict]) -> str:
        """
        C-type pipeline: handles both relay (specialist hand-offs) and
        refinement (each stage improves the same output) depending on
        stage config.

        Each stage dict:
          task_type: str
          system_prompt: str
          user_message: str
          mode: "relay" | "refine"   (default: relay)
          max_tokens: int (optional)
        """
        accumulated_output = ""
        wound_ctx: dict = {}

        for i, stage in enumerate(stages):
            complexity = self._select_complexity(
                stage["task_type"], len(accumulated_output)
            )

            user_msg = stage["user_message"]
            if stage.get("mode") == "refine" and accumulated_output:
                user_msg = f"Previous output to refine:\n{accumulated_output}\n\n{user_msg}"

            task = TaskContext(
                task_id=f"pipeline-stage-{i}-{stage['task_type']}",
                complexity=complexity,
                system_prompt=stage["system_prompt"],
                messages=[{"role": "user", "content": user_msg}],
                max_tokens=stage.get("max_tokens", 4096),
                wound_context=wound_ctx,
            )

            result = self.run_task(task)

            # Wind output for next stage
            wound_ctx = self.wind(result, {"stage": i, "task_type": stage["task_type"]})
            accumulated_output = result

        return accumulated_output

    def _extract_text(self, response) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    def run_with_tools(self, task: TaskContext, tool_executor) -> str:
        """
        Agentic tool-use loop. Model calls tools until it produces a final text response.
        tool_executor: callable(tool_name, tool_input) -> str
        """
        model = self._model_map[task.complexity]
        messages = list(task.messages)

        while True:
            response = self.client.messages.create(
                model=model,
                max_tokens=task.max_tokens,
                system=task.system_prompt,
                messages=messages,
                tools=task.tools,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                assistant_msg = {"role": "assistant", "content": response.content}
                messages.append(assistant_msg)

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info(f"[Movement] Tool call: {block.name}")
                        result = tool_executor(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                return self._extract_text(response)
