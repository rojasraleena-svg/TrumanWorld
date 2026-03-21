from __future__ import annotations

from dataclasses import dataclass, field

from app.scenario.bundle_registry import get_scenario_bundle, resolve_default_scenario_id


@dataclass
class ScenarioRuntimeConfig:
    subject_role: str = "truman"
    support_roles: list[str] = field(default_factory=lambda: ["cast"])
    alert_metric: str = "suspicion_score"
    subject_alert_tracking: bool = True

    def support_role_set(self) -> set[str]:
        return set(self.support_roles)


DEFAULT_NARRATIVE_WORLD_RUNTIME_CONFIG = ScenarioRuntimeConfig(
    subject_role="truman",
    support_roles=["cast"],
    alert_metric="suspicion_score",
    subject_alert_tracking=True,
)

RuntimeRoleSemantics = ScenarioRuntimeConfig


def build_scenario_runtime_config(scenario_id: str) -> ScenarioRuntimeConfig:
    bundle = get_scenario_bundle(scenario_id)
    default_bundle = get_scenario_bundle(resolve_default_scenario_id())
    default_semantics = default_bundle.semantics if default_bundle is not None else None
    default_capabilities = default_bundle.capabilities if default_bundle is not None else None
    semantics = bundle.semantics if bundle is not None else None
    capabilities = bundle.capabilities if bundle is not None else None
    return ScenarioRuntimeConfig(
        subject_role=(
            (semantics.subject_role if semantics is not None else None)
            or (default_semantics.subject_role if default_semantics is not None else None)
            or DEFAULT_NARRATIVE_WORLD_RUNTIME_CONFIG.subject_role
        ),
        support_roles=(
            (semantics.support_roles if semantics is not None else None)
            or (default_semantics.support_roles if default_semantics is not None else None)
            or list(DEFAULT_NARRATIVE_WORLD_RUNTIME_CONFIG.support_roles)
        ),
        alert_metric=(
            (semantics.alert_metric if semantics is not None else None)
            or (default_semantics.alert_metric if default_semantics is not None else None)
            or DEFAULT_NARRATIVE_WORLD_RUNTIME_CONFIG.alert_metric
        ),
        subject_alert_tracking=(
            capabilities.subject_alert_tracking
            if capabilities is not None and capabilities.subject_alert_tracking is not None
            else (
                default_capabilities.subject_alert_tracking
                if default_capabilities is not None
                and default_capabilities.subject_alert_tracking is not None
                else DEFAULT_NARRATIVE_WORLD_RUNTIME_CONFIG.subject_alert_tracking
            )
        ),
    )


def build_runtime_role_semantics(scenario_id: str | None) -> RuntimeRoleSemantics:
    return build_scenario_runtime_config(scenario_id or resolve_default_scenario_id())
