"""
DomainAgent — a plug-and-play complication in The Movement.

Each domain (Finance, Geopolitical, Technology, Risk, etc.) gets one instance.
The agent self-selects tools based on what the domain needs.
"""

import json
from ..movement.orchestrator import Movement, TaskComplexity, TaskContext
from ..tools.web_search import web_search_formatted
from ..tools.financial import format_stock_info, search_tickers
from ..utils.logger import get_logger
from .base import BaseAgent

logger = get_logger("agents.domain")

# Claude tool schemas available to domain agents
AGENT_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current news, analysis, and information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 6},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stock_info",
        "description": "Get financial fundamentals, analyst targets, and metadata for a stock ticker.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "search_tickers",
        "description": "Find stock tickers matching a company name or sector description.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_stock_history",
        "description": "Get historical price performance for a ticker over a given period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {
                    "type": "string",
                    "enum": ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                    "default": "1y",
                },
            },
            "required": ["ticker"],
        },
    },
]


def _execute_tool(name: str, inputs: dict) -> str:
    """Route tool calls to the right function."""
    if name == "web_search":
        return web_search_formatted(inputs["query"], inputs.get("max_results", 6))
    if name == "get_stock_info":
        return format_stock_info(inputs["ticker"])
    if name == "search_tickers":
        results = search_tickers(inputs["query"])
        return json.dumps(results, indent=2) if results else "No tickers found."
    if name == "get_stock_history":
        from ..tools.financial import get_ticker_history
        hist = get_ticker_history(inputs["ticker"], inputs.get("period", "1y"))
        return json.dumps(hist, indent=2)
    return f"Unknown tool: {name}"


# Domain-specific system prompts and focus areas
DOMAIN_CONFIGS = {
    "finance": {
        "system": "You are a senior financial analyst. Your focus: valuations, growth metrics, capital flows, earnings trajectory, analyst consensus, and 5–7 year return potential.",
        "focus": "financial metrics, valuation, growth trajectory, return potential",
    },
    "technology": {
        "system": "You are a deep technology researcher. Your focus: technical moats, innovation roadmaps, R&D pipelines, patent activity, and technological disruption risk.",
        "focus": "technology trends, technical differentiation, innovation pipeline, disruption potential",
    },
    "geopolitical": {
        "system": "You are a geopolitical and macroeconomic analyst. Your focus: trade policy, sanctions, supply chain geopolitics, government policy, war/conflict impacts, and regulatory environment.",
        "focus": "geopolitical risks, trade policy, regulatory landscape, macroeconomic forces",
    },
    "market_sentiment": {
        "system": "You are a market sentiment and behavioral finance analyst. Your focus: institutional positioning, retail sentiment, short interest, narrative cycles, and momentum.",
        "focus": "market sentiment, institutional behavior, narrative trends, momentum signals",
    },
    "risk": {
        "system": "You are a risk assessment specialist. Your focus: downside scenarios, tail risks, competitive threats, execution risk, leverage, and black swan events.",
        "focus": "risk factors, downside scenarios, competitive threats, execution risk",
    },
    "supply_chain": {
        "system": "You are a supply chain and industrial analyst. Your focus: manufacturing capacity, supplier dependencies, logistics bottlenecks, and commodity exposure.",
        "focus": "supply chain resilience, manufacturing capacity, supplier risk, commodity exposure",
    },
    "regulatory": {
        "system": "You are a regulatory and legal analyst. Your focus: antitrust, export controls, data regulation, environmental compliance, and government contract exposure.",
        "focus": "regulatory risk, compliance requirements, legal exposure, government policy",
    },
    "competitive": {
        "system": "You are a competitive intelligence analyst. Your focus: market share dynamics, competitor roadmaps, pricing power, and strategic positioning.",
        "focus": "competitive landscape, market share, pricing power, strategic moats",
    },
}


class DomainAgent(BaseAgent):
    """
    One complication in The Movement. Handles a specific domain's research.
    Self-selects tools. Runs the AutoResearch loop.
    """

    def __init__(self, domain: str, project_id: str, movement: Movement):
        super().__init__(domain, project_id, movement)
        cfg = DOMAIN_CONFIGS.get(domain.lower(), {
            "system": f"You are an expert {domain} analyst.",
            "focus": domain,
        })
        self.system_prompt = cfg["system"]
        self.focus = cfg["focus"]

    def form_initial_hypothesis(self, scope: dict) -> str:
        brief = scope.get("brief", "")
        layers = scope.get("layers", [])
        layer_str = ", ".join(layers) if layers else "the identified sectors"

        return (
            f"Based on the scope '{brief}', from a {self.domain} perspective, "
            f"the most promising opportunities in {layer_str} are those with "
            f"strong {self.focus} fundamentals."
        )

    def research_step(self, scope: dict, hypothesis: str, previous_findings: str) -> dict:
        """
        One research iteration using the mid model with full tool access.
        Returns evidence, confidence score, findings, and approach used.
        """
        brief = scope.get("brief", "")
        layers = scope.get("layers", [])
        tickers = scope.get("suggested_tickers", [])
        clarifications = scope.get("clarifications", {})

        user_message = f"""Research scope: {brief}

Technology/sector layers: {', '.join(layers) if layers else 'as identified'}
Clarified context: {json.dumps(clarifications, indent=2)}
Suggested tickers to investigate: {', '.join(tickers) if tickers else 'identify the best candidates'}

Your current hypothesis:
{hypothesis}

Previous findings to build on:
{previous_findings or 'None — this is the first iteration.'}

Challenger feedback to address:
{self.state.challenger_feedback or 'None yet.'}

Your task:
1. Use your tools to research this scope from a {self.domain} perspective
2. Focus on: {self.focus}
3. For stock research: identify the 3-5 strongest candidates per layer with specific evidence
4. Search for current data, recent news, and analyst perspectives
5. Build on previous findings, don't repeat what's already established

After your research, provide a structured response:
FINDINGS: [detailed analysis]
EVIDENCE: [bullet list of specific data points found]
CONFIDENCE: [0.0-1.0 — how confident are you in these findings given the evidence quality]
APPROACH: [what research angle you used this iteration]
REASONING: [why this confidence level — what would increase it further]"""

        task = TaskContext(
            task_id=f"{self.agent_id}-research-{self.domain}",
            complexity=TaskComplexity.MID,
            system_prompt=self.system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=AGENT_TOOLS,
            max_tokens=4096,
        )

        raw = self.movement.run_with_tools(task, _execute_tool)
        return self._parse_research_output(raw)

    def _parse_research_output(self, raw: str) -> dict:
        """Extract structured fields from the agent's response."""
        result = {
            "findings": raw,
            "evidence": [],
            "confidence": 0.5,
            "approach": "general research",
            "reasoning": "",
        }

        lines = raw.split("\n")
        current_section = None

        for line in lines:
            stripped = line.strip()
            upper = stripped.upper()

            if upper.startswith("FINDINGS:"):
                current_section = "findings"
                result["findings"] = stripped[9:].strip()
            elif upper.startswith("EVIDENCE:"):
                current_section = "evidence"
            elif upper.startswith("CONFIDENCE:"):
                current_section = None
                try:
                    val = stripped[11:].strip().split()[0].rstrip(",.")
                    result["confidence"] = max(0.0, min(1.0, float(val)))
                except (ValueError, IndexError):
                    pass
            elif upper.startswith("APPROACH:"):
                current_section = "approach"
                result["approach"] = stripped[9:].strip()
            elif upper.startswith("REASONING:"):
                current_section = "reasoning"
                result["reasoning"] = stripped[10:].strip()
            elif current_section == "findings" and stripped:
                result["findings"] += "\n" + stripped
            elif current_section == "evidence" and stripped.startswith(("-", "•", "*")):
                result["evidence"].append(stripped.lstrip("-•* "))
            elif current_section in ("approach", "reasoning") and stripped:
                result[current_section] += " " + stripped

        return result
