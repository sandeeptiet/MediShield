"""Prometheus metrics — scraped by OpenShift via ServiceMonitor."""
from prometheus_client import Counter, Histogram

cases_processed = Counter(
    "medishield_cases_total",
    "Cases processed",
    ["decision"],
)

agent_latency = Histogram(
    "medishield_agent_latency_seconds",
    "Per-agent latency",
    ["agent_name"],
)

agent_errors = Counter(
    "medishield_agent_errors_total",
    "Per-agent error counts",
    ["agent_name", "error_type"],
)

auth_attempts = Counter(
    "medishield_auth_attempts_total",
    "Login attempts",
    ["outcome"],  # success | denied | invalid
)
