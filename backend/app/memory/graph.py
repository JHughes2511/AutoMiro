"""
MemoryGraph — persistent cross-project knowledge using Zep Cloud.

Every research session enriches the graph. Agents can query past findings
before starting a new iteration, so the system always builds on prior work.
"""

import json
import time
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger("memory.graph")


class MemoryGraph:
    def __init__(self):
        self._zep = None
        self._available = False
        self._init_zep()

    def _init_zep(self):
        if not Config.ZEP_API_KEY:
            logger.info("[Memory] No ZEP_API_KEY — memory layer disabled, research still works")
            return
        try:
            from zep_cloud.client import Zep
            self._zep = Zep(api_key=Config.ZEP_API_KEY)
            self._available = True
            logger.info("[Memory] Zep connected")
        except Exception as e:
            logger.warning(f"[Memory] Zep init failed: {e} — memory layer disabled")

    def store_project_research(self, project_id: str, scope: dict, synthesis: dict):
        """Persist a completed research round to the memory graph."""
        if not self._available:
            return
        try:
            session_id = f"automiro-{project_id}"
            content = f"""Project: {project_id}
Scope: {scope.get('brief', '')}
Objective: {scope.get('objective', '')}
Layers: {', '.join(scope.get('layers', []))}

Key Findings:
{synthesis.get('final_vision', {}).get('morning_report', '')[:2000]}

Top Picks:
{json.dumps(synthesis.get('final_vision', {}).get('top_picks_by_layer', {}), indent=2)[:1000]}

Convergences:
{json.dumps(synthesis.get('final_vision', {}).get('key_convergences', []), indent=2)}
"""
            self._zep.memory.add(
                session_id=session_id,
                messages=[{
                    "role": "assistant",
                    "role_type": "assistant",
                    "content": content,
                }],
            )
            logger.info(f"[Memory] Stored research for project {project_id}")
        except Exception as e:
            logger.warning(f"[Memory] Store failed: {e}")

    def get_relevant_context(self, project_id: str, query: str) -> str:
        """Retrieve relevant past research for a new research iteration."""
        if not self._available:
            return ""
        try:
            session_id = f"automiro-{project_id}"
            result = self._zep.memory.search(
                session_id=session_id,
                text=query,
                limit=5,
            )
            if not result or not hasattr(result, "results"):
                return ""

            parts = []
            for r in result.results:
                if hasattr(r, "message") and r.message:
                    parts.append(r.message.content)
            return "\n\n".join(parts)
        except Exception as e:
            logger.warning(f"[Memory] Retrieval failed: {e}")
            return ""

    def store_agent_finding(self, project_id: str, domain: str, finding: str, confidence: float):
        """Store an individual agent's finding for cross-project knowledge sharing."""
        if not self._available:
            return
        try:
            session_id = f"automiro-{project_id}-{domain}"
            self._zep.memory.add(
                session_id=session_id,
                messages=[{
                    "role": "assistant",
                    "role_type": "assistant",
                    "content": f"[{domain} | confidence: {confidence:.0%}]\n{finding}",
                }],
            )
        except Exception as e:
            logger.warning(f"[Memory] Agent finding store failed: {e}")

    @property
    def available(self) -> bool:
        return self._available
