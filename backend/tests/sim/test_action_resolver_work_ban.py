"""Tests for work_ban restriction in action_resolver."""

from datetime import datetime


from app.sim.action_resolver import ActionIntent, ActionResolver
from app.sim.world import AgentState, RestrictionState, WorldState


def _build_world() -> WorldState:
    from app.sim.world import LocationState

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
        locations={
            "home": LocationState(id="home", name="Home", location_type="residence"),
            "cafe": LocationState(id="cafe", name="Cafe", location_type="workplace"),
        },
    )


class TestActionResolverWorkBan:
    """Test that action_resolver rejects work when agent has work_ban."""

    def test_work_action_rejected_when_work_ban_active(self):
        """Agent with active work_ban cannot work."""
        world = _build_world()
        # Add work_ban restriction for alice
        world.add_restriction(
            "alice",
            RestrictionState(
                id="ban-1",
                restriction_type="work_ban",
                scope_type="action",
                scope_value="work",
                start_tick=0,
                end_tick=100,
                reason="repeated_warn:noise",
            ),
        )

        resolver = ActionResolver()
        intent = ActionIntent(
            agent_id="alice",
            action_type="work",
        )

        result = resolver.resolve(world, intent)

        assert result.accepted is False
        assert result.reason == "work_ban"

    def test_work_action_allowed_when_work_ban_expired(self):
        """Agent can work after work_ban expires."""
        world = _build_world()
        world.current_tick = 50
        # Add work_ban restriction that ended at tick 30
        world.add_restriction(
            "alice",
            RestrictionState(
                id="ban-expired",
                restriction_type="work_ban",
                scope_type="action",
                scope_value="work",
                start_tick=0,
                end_tick=30,
                reason="block_violation",
            ),
        )

        resolver = ActionResolver()
        intent = ActionIntent(
            agent_id="alice",
            action_type="work",
        )

        result = resolver.resolve(world, intent)

        # work_ban expired, action should be allowed (assuming no other blocks)
        # Note: this will still go through rule evaluation
        assert result.accepted is True

    def test_work_action_allowed_when_no_work_ban(self):
        """Agent without work_ban can work."""
        world = _build_world()

        resolver = ActionResolver()
        intent = ActionIntent(
            agent_id="alice",
            action_type="work",
        )

        result = resolver.resolve(world, intent)

        # No restriction, should be allowed
        assert result.accepted is True

    def test_rest_action_still_allowed_with_work_ban(self):
        """work_ban only blocks work, not rest."""
        world = _build_world()
        world.add_restriction(
            "alice",
            RestrictionState(
                id="ban-1",
                restriction_type="work_ban",
                scope_type="action",
                scope_value="work",
                start_tick=0,
                end_tick=100,
                reason="repeated_warn:noise",
            ),
        )

        resolver = ActionResolver()
        intent = ActionIntent(
            agent_id="alice",
            action_type="rest",
        )

        result = resolver.resolve(world, intent)

        assert result.accepted is True

    def test_move_action_still_allowed_with_work_ban(self):
        """work_ban only blocks work, not move."""
        world = _build_world()
        world.add_restriction(
            "alice",
            RestrictionState(
                id="ban-1",
                restriction_type="work_ban",
                scope_type="action",
                scope_value="work",
                start_tick=0,
                end_tick=100,
                reason="repeated_warn:noise",
            ),
        )

        resolver = ActionResolver()
        intent = ActionIntent(
            agent_id="alice",
            action_type="move",
            target_location_id="cafe",
        )

        result = resolver.resolve(world, intent)

        assert result.accepted is True
