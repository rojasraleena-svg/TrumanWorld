"""Deterministic governance execution for world rule outcomes."""

from __future__ import annotations

from app.scenario.runtime.world_design_models import (
    GovernanceExecutionResult,
    RuleEvaluationResult,
    WorldDesignRuntimePackage,
)
from app.sim.world import WorldState

if False:  # pragma: no cover
    from app.sim.action_resolver import ActionIntent


def execute_governance(
    *,
    world: WorldState,
    intent: "ActionIntent",
    rule_evaluation: RuleEvaluationResult | None,
    package: WorldDesignRuntimePackage,
) -> GovernanceExecutionResult:
    if rule_evaluation is None:
        return GovernanceExecutionResult(
            decision="allow",
            reason="no_rule_evaluation",
            enforcement_action="none",
        )

    if rule_evaluation.decision == "allowed":
        return GovernanceExecutionResult(
            decision="allow",
            reason=rule_evaluation.reason or "allowed",
            enforcement_action="none",
        )

    if rule_evaluation.decision == "impossible":
        return GovernanceExecutionResult(
            decision="block",
            reason=rule_evaluation.reason or "impossible",
            enforcement_action="intercept",
            matched_signals=["physical_or_system_constraint"],
        )

    policy_values = package.policy_config.values or {}
    inspection_level = str(policy_values.get("inspection_level") or "medium")
    high_attention_locations = _normalize_str_list(policy_values.get("high_attention_locations"))
    sensitive_locations = _normalize_str_list(policy_values.get("sensitive_locations"))

    signals = list(rule_evaluation.matched_tags)
    current_location_id = intent.target_location_id or world.get_agent(intent.agent_id).location_id
    if current_location_id in high_attention_locations:
        signals.append("high_attention_location")
    if current_location_id in sensitive_locations:
        signals.append("sensitive_location")

    if rule_evaluation.decision == "soft_risk":
        return GovernanceExecutionResult(
            decision="warn",
            reason=rule_evaluation.reason or "soft_risk_warning",
            enforcement_action="warning",
            matched_signals=sorted(set(signals)),
        )

    if "subject" in signals or "sensitive_location" in signals:
        return GovernanceExecutionResult(
            decision="block",
            reason=rule_evaluation.reason or "policy_blocked",
            enforcement_action="intercept",
            matched_signals=sorted(set(signals)),
        )

    if inspection_level == "low":
        return GovernanceExecutionResult(
            decision="warn",
            reason=rule_evaluation.reason or "policy_warning",
            enforcement_action="warning",
            matched_signals=sorted(set(signals)),
        )

    return GovernanceExecutionResult(
        decision="block",
        reason=rule_evaluation.reason or "policy_blocked",
        enforcement_action="intercept",
        matched_signals=sorted(set(signals)),
    )


def _normalize_str_list(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}
