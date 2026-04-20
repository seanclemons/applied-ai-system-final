import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "session.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("vibefinder")


def log_agent_step(step_num: int, step_name: str, detail: str = ""):
    logger.info(f"[STEP {step_num}] {step_name}" + (f" | {detail}" if detail else ""))


def log_guardrail(field: str, issue: str):
    logger.warning(f"[GUARDRAIL] {field}: {issue}")


def log_retrieval(query: str, hits: int, sources: list):
    logger.info(f"[RETRIEVAL] query='{query}' hits={hits} sources={sources}")


def log_confidence(title: str, score: float, confidence: float):
    logger.info(f"[CONFIDENCE] '{title}' raw_score={score:.3f} confidence={confidence:.2f}")


def log_critique(issue: str):
    logger.warning(f"[SELF-CRITIQUE] {issue}")


def log_error(context: str, error: Exception):
    logger.error(f"[ERROR] {context}: {error}")
