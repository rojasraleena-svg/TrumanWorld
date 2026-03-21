from datetime import datetime

from app.scenario.runtime.world_design_models import GovernanceExecutionResult
from app.sim.action_resolver import ActionResult
from app.sim.governance_consequences import apply_governance_consequences
from app.sim.world import AgentState, WorldState


def _build_world() -> WorldState:
    return WorldState(
        current_time=datetime(2026, 3, 7, 8, 0, 0),
        agents={
            "alice": AgentState(
                id="alice",
                name="Alice",
                location_id="home",
                status={},
            )
        },
        locations={},
    )


def test_apply_governance_consequences_warn_updates_status():
    world = _build_world()
    result = ActionResult(
        accepted=True,
        action_type="move",
        reason="accepted",
        event_payload={"agent_id": "alice"},
        governance_execution=GovernanceExecutionResult(
            decision="warn",
            reason="location_closed",
            enforcement_action="warning",
        ),
    )

    apply_governance_consequences(world, result)

    assert world.agents["alice"].status["warning_count"] == 1
    assert world.agents["alice"].status["governance_attention_score"] == 0.05


def test_apply_governance_consequences_block_adds_stronger_attention():
    world = _build_world()
    world.agents["alice"].status = {"warning_count": 1, "governance_attention_score": 0.2}
    result = ActionResult(
        accepted=False,
        action_type="move",
        reason="location_closed",
        event_payload={"agent_id": "alice"},
        governance_execution=GovernanceExecutionResult(
            decision="block",
            reason="location_closed",
            enforcement_action="intercept",
        ),
    )

    apply_governance_consequences(world, result)

    assert world.agents["alice"].status["warning_count"] == 2
    assert world.agents["alice"].status["governance_attention_score"] == 0.35


def test_apply_governance_consequences_caps_attention_score():
    world = _build_world()
    world.agents["alice"].status = {"warning_count": 3, "governance_attention_score": 0.95}
    result = ActionResult(
        accepted=False,
        action_type="move",
        reason="location_closed",
        event_payload={"agent_id": "alice"},
        governance_execution=GovernanceExecutionResult(
            decision="block",
            reason="location_closed",
            enforcement_action="intercept",
        ),
    )

    apply_governance_consequences(world, result)

    assert world.agents["alice"].status["warning_count"] == 4
    assert world.agents["alice"].status["governance_attention_score"] == 1.0


def test_apply_governance_consequences_ignores_allow():
    world = _build_world()
    result = ActionResult(
        accepted=True,
        action_type="rest",
        reason="accepted",
        event_payload={"agent_id": "alice"},
        governance_execution=GovernanceExecutionResult(
            decision="allow",
            reason="rest_allowed",
            enforcement_action="none",
        ),
    )

    apply_governance_consequences(world, result)

    assert world.agents["alice"].status == {}
