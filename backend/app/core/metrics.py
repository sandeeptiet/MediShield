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

http_requests = Counter(
    "medishield_http_requests_total",
    "HTTP requests served",
    ["method", "route", "status_code"],
)

http_request_duration = Histogram(
    "medishield_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "route"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
