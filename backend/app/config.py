import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Claude API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Model assignments — The Movement barrel definitions
    MODEL_FAST = os.getenv("MODEL_FAST", "claude-haiku-4-5-20251001")       # Barrel 1: data gather, drafts
    MODEL_MID = os.getenv("MODEL_MID", "claude-sonnet-4-6")                  # Barrel 2: analysis, domain work
    MODEL_HEAVY = os.getenv("MODEL_HEAVY", "claude-opus-4-7")                # Heavy: synthesis, final vision

    # Zep memory
    ZEP_API_KEY = os.getenv("ZEP_API_KEY", "")

    # Agent runtime
    MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "8"))
    AGENT_ITERATION_LIMIT = int(os.getenv("AGENT_ITERATION_LIMIT", "5"))     # AutoResearch loop cap per agent
    RESEARCH_TIMEOUT_SECONDS = int(os.getenv("RESEARCH_TIMEOUT_SECONDS", "300"))

    # Flask
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "automiro-dev-key")

    # Storage (local file-based for free tier)
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    PROJECTS_DIR = os.path.join(DATA_DIR, "projects")
    REPORTS_DIR = os.path.join(DATA_DIR, "reports")
