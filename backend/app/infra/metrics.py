from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    GCCollector,
    Gauge,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)

from app.sim.scheduler import get_scheduler


REGISTRY = CollectorRegistry()
ProcessCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)
GCCollector(registry=REGISTRY)

TICK_TOTAL = Counter(
    "trumanworld_tick_total",
    "Total number of simulation ticks executed.",
    labelnames=("mode", "status"),
    registry=REGISTRY,
)

TICK_DURATION_SECONDS = Histogram(
    "trumanworld_tick_duration_seconds",
    "Simulation tick execution duration in seconds.",
    labelnames=("mode",),
    registry=REGISTRY,
)

ACTIVE_RUNS = Gauge(
    "trumanworld_active_runs",
    "Number of currently scheduled runs.",
    registry=REGISTRY,
)
ACTIVE_RUNS.set_function(lambda: get_scheduler().running_count())

LLM_CALL_TOTAL = Counter(
    "trumanworld_llm_call_total",
    "Total persisted LLM calls.",
    registry=REGISTRY,
)

LLM_TOKENS_TOTAL = Counter(
    "trumanworld_llm_tokens_total",
    "Total persisted LLM tokens by type.",
    labelnames=("token_type",),
    registry=REGISTRY,
)

LLM_COST_USD_TOTAL = Counter(
    "trumanworld_llm_cost_usd_total",
    "Total persisted LLM cost in USD.",
    registry=REGISTRY,
)


def observe_tick(*, mode: str, status: str, duration_seconds: float) -> None:
    TICK_TOTAL.labels(mode=mode, status=status).inc()
    TICK_DURATION_SECONDS.labels(mode=mode).observe(duration_seconds)


def observe_llm_records(llm_records: list) -> None:
    for record in llm_records:
        LLM_CALL_TOTAL.inc()
        LLM_TOKENS_TOTAL.labels(token_type="input").inc(record.input_tokens or 0)
        LLM_TOKENS_TOTAL.labels(token_type="output").inc(record.output_tokens or 0)
        LLM_TOKENS_TOTAL.labels(token_type="cache_read").inc(record.cache_read_tokens or 0)
        LLM_TOKENS_TOTAL.labels(token_type="cache_creation").inc(record.cache_creation_tokens or 0)
        if record.total_cost_usd:
            LLM_COST_USD_TOTAL.inc(record.total_cost_usd)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
