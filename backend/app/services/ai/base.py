"""BaseAgent — shared scaffolding for every agent node in the LangGraph.

Each concrete agent implements `process(state)` and returns a dict patch to
merge into the AgentState. BaseAgent wraps that with:
  - structlog event per call
  - Prometheus latency + error metrics
  - try/except that captures errors into state.errors rather than crashing the graph
  - LangSmith tracing happens automatically when LANGSMITH_TRACING=true
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import get_logger
from app.core.metrics import agent_errors, agent_latency
from app.services.ai.state import AgentError, AgentState


class BaseAgent(ABC):
    """Concrete agents subclass this and implement `process()`."""

    #: Short identifier used in logs, metrics, and audit rows.
    name: str = "base"

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.name}")

    # --- The public entrypoint LangGraph calls -----------------------

    def __call__(self, state: AgentState) -> dict[str, Any]:
        case_id = state.get("case_id", "?")
        self.logger.info("agent.start", case_id=case_id)
        started = time.perf_counter()

        try:
            with agent_latency.labels(agent_name=self.name).time():
                patch = self.process(state)
        except Exception as exc:
            elapsed = time.perf_counter() - started
            agent_errors.labels(agent_name=self.name, error_type=type(exc).__name__).inc()
            self.logger.exception(
                "agent.error",
                case_id=case_id,
                error_type=type(exc).__name__,
                elapsed_ms=int(elapsed * 1000),
            )
            return _append_error(state, self.name, exc)

        elapsed = time.perf_counter() - started
        self.logger.info("agent.ok", case_id=case_id, elapsed_ms=int(elapsed * 1000))
        return patch

    # --- The hook concrete agents implement --------------------------

    @abstractmethod
    def process(self, state: AgentState) -> dict[str, Any]:
        """Run the agent and return a partial-state dict to merge.

        Must NOT mutate the input state. Must NOT raise for expected business
        outcomes (e.g. "not covered" is still a successful run).
        """


def _append_error(state: AgentState, agent_name: str, exc: Exception) -> dict[str, Any]:
    existing: list[AgentError] = list(state.get("errors", []))
    existing.append({"agent": agent_name, "type": type(exc).__name__, "message": str(exc)})
    return {"errors": existing}


__all__ = ["BaseAgent"]
