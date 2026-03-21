from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.scenario.bundle_world.heuristics import build_bundle_world_decision
from app.scenario.bundle_world.seed import BundleWorldSeedBuilder
from app.scenario.bundle_world.state import BundleWorldStateUpdater
from app.scenario.bundle_world.types import BundleWorldGuidance, build_bundle_world_guidance
from app.scenario.runtime_config import RuntimeRoleSemantics
from app.sim.action_resolver import ActionIntent
from app.sim.types import RuntimeWorldContext


class DefaultFallbackPolicy:
    def __init__(self, *, scenario_id: str, semantics: RuntimeRoleSemantics) -> None:
        self.scenario_id = scenario_id
        self.semantics = semantics

    def configure_runtime(self, agent_runtime) -> None:
        agent_runtime.configure_fallback_decision_hook(self.build_runtime_decision)

    def build_runtime_decision(
        self,
        world: RuntimeWorldContext,
        nearby_agent_id: str | None,
        current_location_id: str | None,
        home_location_id: str | None,
        agent_id: str | None = None,
    ):
        return build_bundle_world_decision(
            world=world,
            nearby_agent_id=nearby_agent_id,
            current_location_id=current_location_id,
            home_location_id=home_location_id,
            agent_id=agent_id,
            semantics=self.semantics,
        )

    def fallback_intent(
        self,
        *,
        agent_id: str,
        current_location_id: str,
        home_location_id: str | None,
        nearby_agent_id: str | None,
        world_role: str | None = None,
        current_status: dict | None = None,
        scenario_state: dict | None = None,
        scenario_guidance=None,
    ) -> ActionIntent | None:
        subject_alert_score = float((scenario_state or {}).get("subject_alert_score") or 0.0)
        director_guidance: BundleWorldGuidance = {}
        if scenario_guidance:
            director_guidance = build_bundle_world_guidance(
                scene_goal=scenario_guidance.get("scene_goal")
                or scenario_guidance.get("director_scene_goal"),
                priority=scenario_guidance.get("priority")
                or scenario_guidance.get("director_priority"),
                message_hint=scenario_guidance.get("message_hint")
                or scenario_guidance.get("director_message_hint"),
                target_agent_id=scenario_guidance.get("target_agent_id")
                or scenario_guidance.get("director_target_agent_id"),
                location_hint=scenario_guidance.get("location_hint")
                or scenario_guidance.get("director_location_hint"),
                reason=scenario_guidance.get("reason") or scenario_guidance.get("director_reason"),
            )
        runtime_world: RuntimeWorldContext = {
            "world_role": world_role,
            "self_status": current_status or {},
            "subject_alert_score": subject_alert_score,
            **director_guidance,
        }
        decision = build_bundle_world_decision(
            world=runtime_world,
            nearby_agent_id=nearby_agent_id,
            current_location_id=current_location_id,
            home_location_id=home_location_id,
            semantics=self.semantics,
        )
        if decision is None:
            return None
        payload = dict(decision.payload)
        if decision.message:
            payload["message"] = decision.message
        return ActionIntent(
            agent_id=agent_id,
            action_type=decision.action_type,
            target_location_id=decision.target_location_id,
            target_agent_id=decision.target_agent_id,
            payload=payload,
        )


FallbackPolicyFactory = Callable[..., Any]
SeedPolicyFactory = Callable[..., Any]
StateUpdatePolicyFactory = Callable[..., Any]


@dataclass
class BundleWorldModuleRegistry:
    fallback_policies: dict[str, FallbackPolicyFactory] = field(default_factory=dict)
    seed_policies: dict[str, SeedPolicyFactory] = field(default_factory=dict)
    state_update_policies: dict[str, StateUpdatePolicyFactory] = field(default_factory=dict)

    def register_fallback_policy(self, module_id: str, factory: FallbackPolicyFactory) -> None:
        self.fallback_policies[module_id] = factory

    def register_seed_policy(self, module_id: str, factory: SeedPolicyFactory) -> None:
        self.seed_policies[module_id] = factory

    def register_state_update_policy(
        self, module_id: str, factory: StateUpdatePolicyFactory
    ) -> None:
        self.state_update_policies[module_id] = factory

    def build_fallback_policy(self, module_id: str, **kwargs):
        return self.fallback_policies[module_id](**kwargs)

    def build_seed_policy(self, module_id: str, *args, **kwargs):
        return self.seed_policies[module_id](*args, **kwargs)

    def build_state_update_policy(self, module_id: str, *args, **kwargs):
        return self.state_update_policies[module_id](*args, **kwargs)


_registry = BundleWorldModuleRegistry()
_registry.register_fallback_policy("social_default", DefaultFallbackPolicy)
_registry.register_seed_policy("standard_bundle_seed", BundleWorldSeedBuilder)
_registry.register_state_update_policy("alert_tracking", BundleWorldStateUpdater)


def get_bundle_world_module_registry() -> BundleWorldModuleRegistry:
    return _registry
