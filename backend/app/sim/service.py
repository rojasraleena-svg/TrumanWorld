"""Simulation service for running ticks and managing world state.

This module provides the main SimulationService class that orchestrates
simulation ticks, agent decisions, and persistence.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.providers import (
    build_cast_stabilizing_decision,
    build_default_talk_message,
    build_suspicion_aware_decision,
)
from app.agent.registry import AgentRegistry
from app.agent.runtime import AgentRuntime
from app.director.observer import DirectorAssessment, DirectorObserver
from app.director.planner import DirectorPlanner
from app.infra.settings import get_settings
from app.sim.action_resolver import ActionIntent
from app.sim.context import ContextBuilder
from app.sim.persistence import PersistenceManager
from app.sim.runner import SimulationRunner, TickResult
from app.sim.world import AgentState, LocationState, WorldState
from app.store.repositories import (
    AgentRepository,
    EventRepository,
    LocationRepository,
    RunRepository,
    build_event,
)
from app.store.models import Agent, Location

if TYPE_CHECKING:
    from app.infra.db import async_engine


class SimulationService:
    """Loads persisted state, executes one tick, and persists results."""

    DEFAULT_WORLD_START_TIME = datetime(2026, 3, 2, 7, 0, tzinfo=UTC)

    def __init__(
        self,
        session: AsyncSession,
        agent_runtime: AgentRuntime | None = None,
        agents_root: Path | None = None,
    ) -> None:
        self.session = session
        self.run_repo = RunRepository(session)
        self.agent_repo = AgentRepository(session)
        self.location_repo = LocationRepository(session)
        self.event_repo = EventRepository(session)
        self._context_builder = ContextBuilder(session)
        self._persistence = PersistenceManager(session)
        settings = get_settings()
        self.agent_runtime = agent_runtime or AgentRuntime(
            registry=AgentRegistry(agents_root or (settings.project_root / "agents"))
        )

    @classmethod
    def create_for_scheduler(cls, agent_runtime: AgentRuntime) -> "SimulationService":
        """Create a SimulationService instance for scheduler use.

        This factory method creates a service instance that is not bound
        to a specific database session. It should only be used with
        run_tick_isolated() method which manages its own sessions.
        """
        instance = cls.__new__(cls)
        instance.session = None  # type: ignore[assignment]
        instance.agent_runtime = agent_runtime
        instance._context_builder = None  # type: ignore[assignment]
        instance._persistence = None  # type: ignore[assignment]
        return instance

    async def run_tick(self, run_id: str, intents: list[ActionIntent] | None = None) -> TickResult:
        run = await self.run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)

        world = await self._load_world(run_id, tick_minutes=run.tick_minutes)
        if not intents:
            intents = await self.prepare_tick_intents(run_id, world)
        runner = SimulationRunner(world)
        runner.tick_no = run.current_tick
        result = runner.tick(intents)

        await self._persistence.persist_agent_locations(run_id, world)
        await self.run_repo.update_tick(run, result.tick_no)
        await self._persist_tick_events(run_id, result)
        return result

    async def run_tick_isolated(
        self,
        run_id: str,
        engine: "async_engine",
        intents: list[ActionIntent] | None = None,
    ) -> TickResult:
        """Run a tick with isolated database sessions to avoid greenlet conflicts.

        This method separates database operations from SDK calls:
        1. Read phase: Load all needed data from database
        2. SDK phase: Call agent runtime (without active database session)
        3. Write phase: Persist results with a fresh database session

        This prevents conflicts between SQLAlchemy's greenlet mechanism and
        anyio's task groups used by claude_agent_sdk.
        """
        from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionType

        # Phase 1: Read all data needed for the tick
        async with AsyncSessionType(engine) as read_session:
            read_repo = RunRepository(read_session)
            run = await read_repo.get(run_id)
            if run is None:
                msg = f"Run not found: {run_id}"
                raise ValueError(msg)

            tick_minutes = run.tick_minutes
            current_tick = run.current_tick

            # Load locations and agents
            location_repo = LocationRepository(read_session)
            agent_repo = AgentRepository(read_session)
            locations = await location_repo.list_for_run(run_id)
            agents = await agent_repo.list_for_run(run_id)

            # Build world state (copy data before session closes)
            location_states = {
                loc.id: LocationState(
                    id=loc.id,
                    name=loc.name,
                    capacity=loc.capacity,
                    occupants=set(),
                )
                for loc in locations
            }

            agent_states: dict[str, AgentState] = {}
            agent_data: list[dict] = []  # Store agent data for later use

            # First pass: build agent_states and location_states.occupants
            for agent in agents:
                location_id = agent.current_location_id or agent.home_location_id
                if location_id is None:
                    location_id = next(iter(location_states.keys()), "unknown")

                agent_states[agent.id] = AgentState(
                    id=agent.id,
                    name=agent.name,
                    location_id=location_id,
                    status=agent.status or {},
                )
                if location_id in location_states:
                    location_states[location_id].occupants.add(agent.id)

            # Load recent events for all agents (after agent_states is built)
            agent_recent_events: dict[str, list[dict]] = {}
            context_builder = ContextBuilder(read_session)
            for agent in agents:
                recent_events = await agent_repo.list_recent_events(run_id, agent.id, limit=5)
                agent_recent_events[agent.id] = [
                    context_builder.format_event_for_context(evt, agent_states, location_states)
                    for evt in recent_events
                ]

            # Second pass: build agent_data
            observer = DirectorObserver()
            planner = DirectorPlanner()
            assessment = observer.assess(
                run_id=run_id,
                current_tick=current_tick,
                agents=list(agents),
                events=[],
            )
            plan = planner.build_plan(assessment=assessment, agents=list(agents))

            for agent in agents:
                location_id = agent.current_location_id or agent.home_location_id
                if location_id is None:
                    location_id = next(iter(location_states.keys()), "unknown")

                profile = dict(agent.profile or {})
                if plan and agent.id in plan.target_cast_ids:
                    profile.update(
                        {
                            "director_scene_goal": plan.scene_goal,
                            "director_priority": plan.priority,
                            "director_message_hint": plan.message_hint,
                            "director_target_agent_id": plan.target_agent_id,
                            "director_location_hint": plan.location_hint,
                            "director_reason": plan.reason,
                        }
                    )

                agent_data.append(
                    {
                        "id": agent.id,
                        "current_goal": agent.current_goal,
                        "current_location_id": location_id,
                        "home_location_id": agent.home_location_id,
                        "profile": profile,
                        "recent_events": agent_recent_events.get(agent.id, []),
                    }
                )

            world = WorldState(
                current_time=self._get_run_world_time(run),
                tick_minutes=tick_minutes,
                locations=location_states,
                agents=agent_states,
            )

        # Phase 2: Prepare intents (SDK calls happen here, no active session)
        if not intents:
            intents = await self._prepare_intents_from_data(world, agent_data, engine, run_id)

        # Run simulation logic
        runner = SimulationRunner(world)
        runner.tick_no = current_tick
        result = runner.tick(intents)

        # Phase 3: Persist results with a fresh session
        async with AsyncSessionType(engine, expire_on_commit=False) as write_session:
            persistence = PersistenceManager(write_session)
            await persistence.persist_tick_results(
                run_id, result, world, current_tick + 1
            )

        return result

    async def _prepare_intents_from_data(
        self,
        world: WorldState,
        agent_data: list[dict],
        engine: "async_engine | None" = None,
        run_id: str | None = None,
    ) -> list[ActionIntent]:
        """Prepare intents from pre-loaded agent data.

        This method is called without an active database session,
        allowing SDK calls to use anyio without greenlet conflicts.

        Agent decisions are made in PARALLEL for performance.
        Memory tools are available via MCP if engine is provided.
        """
        from app.agent.runtime import RuntimeContext

        async def decide_for_agent(agent_dict: dict) -> ActionIntent:
            """Make decision for a single agent."""
            agent_id = agent_dict["id"]
            state = world.get_agent(agent_id)
            if state is None:
                return None

            nearby_agent_id = ContextBuilder._find_nearby_agent_impl(
                world, agent_id, state.location_id
            )
            profile = agent_dict.get("profile", {})
            runtime_agent_id = profile.get("agent_config_id") or agent_id
            truman_suspicion_score = ContextBuilder._extract_truman_suspicion_from_agent_data_impl(
                agent_data, world
            )

            # Build runtime context with memory tools support
            runtime_ctx = None
            if engine is not None and run_id is not None:
                runtime_ctx = RuntimeContext(
                    db_engine=engine,
                    run_id=run_id,
                    enable_memory_tools=True,
                )

            try:
                intent = await self.agent_runtime.react(
                    runtime_agent_id,
                    world=ContextBuilder._build_agent_world_context_impl(
                        world=world,
                        current_goal=agent_dict.get("current_goal"),
                        current_location_id=agent_dict.get("current_location_id"),
                        home_location_id=agent_dict.get("home_location_id"),
                        nearby_agent_id=nearby_agent_id,
                        current_status=state.status,
                        truman_suspicion_score=truman_suspicion_score,
                        world_role=(
                            profile.get("world_role") if isinstance(profile, dict) else None
                        ),
                        director_scene_goal=(
                            profile.get("director_scene_goal") if isinstance(profile, dict) else None
                        ),
                        director_priority=(
                            profile.get("director_priority") if isinstance(profile, dict) else None
                        ),
                        director_message_hint=(
                            profile.get("director_message_hint")
                            if isinstance(profile, dict)
                            else None
                        ),
                        director_target_agent_id=(
                            profile.get("director_target_agent_id")
                            if isinstance(profile, dict)
                            else None
                        ),
                        director_location_hint=(
                            profile.get("director_location_hint")
                            if isinstance(profile, dict)
                            else None
                        ),
                        director_reason=(
                            profile.get("director_reason") if isinstance(profile, dict) else None
                        ),
                    ),
                    memory={"recent": []},  # Memory tools available via MCP
                    event={},
                    recent_events=agent_dict.get("recent_events", []),
                    runtime_ctx=runtime_ctx,
                )
                intent.agent_id = agent_id
                return intent
            except (RuntimeError, ValueError, asyncio.CancelledError):
                return self._fallback_intent(
                    agent_id=agent_id,
                    current_goal=agent_dict.get("current_goal"),
                    current_location_id=agent_dict.get("current_location_id"),
                    home_location_id=agent_dict.get("home_location_id"),
                    nearby_agent_id=nearby_agent_id,
                    world_role=(profile.get("world_role") if isinstance(profile, dict) else None),
                    current_status=state.status,
                    truman_suspicion_score=truman_suspicion_score,
                    director_scene_goal=(
                        profile.get("director_scene_goal") if isinstance(profile, dict) else None
                    ),
                    director_priority=(
                        profile.get("director_priority") if isinstance(profile, dict) else None
                    ),
                )

        # Execute all agent decisions in PARALLEL
        results = await asyncio.gather(*[decide_for_agent(a) for a in agent_data])

        # Filter out None results (agents without valid state)
        intents = [r for r in results if r is not None]
        return intents

    async def _persist_tick_events(self, run_id: str, result: TickResult) -> None:
        """Persist tick events and related data."""
        events = [
            build_event(
                run_id=run_id,
                tick_no=result.tick_no,
                world_time=result.world_time,
                action_type=item.action_type,
                payload=item.event_payload,
                accepted=True,
            )
            for item in result.accepted
        ]
        events.extend(
            build_event(
                run_id=run_id,
                tick_no=result.tick_no,
                world_time=result.world_time,
                action_type=item.action_type,
                payload={"reason": item.reason, **item.event_payload},
                accepted=False,
            )
            for item in result.rejected
        )
        if events:
            persisted = await self.event_repo.create_many(events)
            await self._persistence.persist_tick_memories(run_id, persisted)
            await self._persistence.persist_tick_relationships(run_id, persisted)
            await self._persistence.persist_truman_suspicion(run_id, persisted)

    async def prepare_tick_intents(self, run_id: str, world: WorldState) -> list[ActionIntent]:
        agents = await self.agent_repo.list_for_run(run_id)
        intents: list[ActionIntent] = []
        truman_suspicion_score = self._context_builder.extract_truman_suspicion_from_agents(
            agents, world
        )
        plan = await self._build_director_plan(run_id, agents)

        for agent in agents:
            state = world.get_agent(agent.id)
            if state is None:
                continue

            nearby_agent_id = self._context_builder.find_nearby_agent(
                world, agent.id, state.location_id
            )
            runtime_agent_id = self._resolve_runtime_agent_id(agent)
            profile = self._context_builder.profile_with_director_plan(agent, plan)
            try:
                intent = await self.agent_runtime.react(
                    runtime_agent_id,
                    world=self._context_builder.build_agent_world_context(
                        world=world,
                        current_goal=agent.current_goal,
                        current_location_id=state.location_id,
                        home_location_id=agent.home_location_id,
                        nearby_agent_id=nearby_agent_id,
                        current_status=state.status,
                        truman_suspicion_score=truman_suspicion_score,
                        world_role=profile.get("world_role"),
                        director_scene_goal=profile.get("director_scene_goal"),
                        director_priority=profile.get("director_priority"),
                        director_message_hint=profile.get("director_message_hint"),
                        director_target_agent_id=profile.get("director_target_agent_id"),
                        director_location_hint=profile.get("director_location_hint"),
                        director_reason=profile.get("director_reason"),
                    ),
                    memory={"recent": []},
                    event={},
                )
                intent.agent_id = agent.id
                intents.append(intent)
            except (RuntimeError, ValueError, asyncio.CancelledError):
                intents.append(
                    self._fallback_intent(
                        agent_id=agent.id,
                        current_goal=agent.current_goal,
                        current_location_id=state.location_id,
                        home_location_id=agent.home_location_id,
                        nearby_agent_id=nearby_agent_id,
                        world_role=profile.get("world_role"),
                        current_status=state.status,
                        truman_suspicion_score=truman_suspicion_score,
                        director_scene_goal=profile.get("director_scene_goal"),
                        director_priority=profile.get("director_priority"),
                    )
                )

        return intents

    def _resolve_runtime_agent_id(self, agent: Agent) -> str:
        profile = agent.profile or {}
        configured_id = profile.get("agent_config_id")
        if isinstance(configured_id, str) and configured_id:
            return configured_id
        return agent.id

    async def inject_director_event(
        self,
        run_id: str,
        event_type: str,
        payload: dict,
        location_id: str | None = None,
        importance: float = 0.5,
    ) -> None:
        run = await self.run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)

        event = build_event(
            run_id=run_id,
            tick_no=run.current_tick,
            world_time=self._get_run_world_time(run).isoformat(),
            action_type=f"director_{event_type}",
            payload=payload,
            accepted=True,
        )
        event.location_id = location_id
        event.importance = importance
        event.visibility = "system"
        await self.event_repo.create(event)

    async def observe_run(self, run_id: str, event_limit: int = 20) -> DirectorAssessment:
        run = await self.run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)

        agents = await self.agent_repo.list_for_run(run_id)
        events = await self.event_repo.list_for_run(run_id, limit=event_limit)

        observer = DirectorObserver()
        return observer.assess(
            run_id=run_id,
            current_tick=run.current_tick,
            agents=list(agents),
            events=list(events),
        )

    async def seed_demo_run(self, run_id: str) -> None:
        run = await self.run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)

        existing_agents = await self.agent_repo.list_for_run(run_id)
        if existing_agents:
            return

        plaza = Location(
            id=f"{run_id}-plaza",
            run_id=run_id,
            name="Town Plaza",
            location_type="plaza",
            capacity=10,
            x=0,
            y=0,
            attributes={"kind": "social"},
        )
        apartment = Location(
            id=f"{run_id}-apartment",
            run_id=run_id,
            name="Seaside Apartment",
            location_type="home",
            capacity=3,
            x=-1,
            y=0,
            attributes={"kind": "private"},
        )
        office = Location(
            id=f"{run_id}-office",
            run_id=run_id,
            name="Harbor Office",
            location_type="office",
            capacity=6,
            x=2,
            y=0,
            attributes={"kind": "work"},
        )
        cafe = Location(
            id=f"{run_id}-cafe",
            run_id=run_id,
            name="Corner Cafe",
            location_type="cafe",
            capacity=6,
            x=1,
            y=0,
            attributes={"kind": "work"},
        )
        truman = Agent(
            id=f"{run_id}-truman",
            run_id=run_id,
            name="Truman",
            occupation="insurance clerk",
            home_location_id=f"{run_id}-apartment",
            current_location_id=f"{run_id}-apartment",
            current_goal="work",
            personality={"openness": 0.55, "conscientiousness": 0.62},
            profile={
                "bio": "Lives an ordinary life and believes the town is completely normal.",
                "agent_config_id": "truman",
                "world_role": "truman",
            },
            status={"energy": 0.85, "suspicion_score": 0.0},
            current_plan={"morning": "commute", "daytime": "work", "evening": "socialize"},
        )
        spouse = Agent(
            id=f"{run_id}-spouse",
            run_id=run_id,
            name="Meryl",
            occupation="hospital staff",
            home_location_id=f"{run_id}-apartment",
            current_location_id=f"{run_id}-apartment",
            current_goal="work",
            personality={"agreeableness": 0.72, "conscientiousness": 0.7},
            profile={
                "bio": "Keeps Truman's domestic life stable and predictable.",
                "agent_config_id": "spouse",
                "world_role": "cast",
            },
            status={"energy": 0.78},
            current_plan={"morning": "prepare_day", "daytime": "work", "evening": "home"},
        )
        friend = Agent(
            id=f"{run_id}-friend",
            run_id=run_id,
            name="Marlon",
            occupation="office coworker",
            home_location_id=f"{run_id}-plaza",
            current_location_id=f"{run_id}-office",
            current_goal="work",
            personality={"agreeableness": 0.68, "openness": 0.48},
            profile={
                "bio": "A familiar friend who often shares Truman's daily routine.",
                "agent_config_id": "friend",
                "world_role": "cast",
            },
            status={"energy": 0.74},
            current_plan={"morning": "work", "daytime": "work", "evening": "socialize"},
        )
        neighbor = Agent(
            id=f"{run_id}-neighbor",
            run_id=run_id,
            name="Lauren",
            occupation="shop regular",
            home_location_id=f"{run_id}-plaza",
            current_location_id=f"{run_id}-cafe",
            current_goal="talk",
            personality={"agreeableness": 0.58, "openness": 0.66},
            profile={
                "bio": "A recurring familiar face around the plaza and cafe.",
                "agent_config_id": "neighbor",
                "world_role": "cast",
            },
            status={"energy": 0.72},
            current_plan={"morning": "socialize", "daytime": "wander", "evening": "socialize"},
        )

        if "world_start_time" not in (run.metadata_json or {}):
            metadata = dict(run.metadata_json or {})
            metadata["world_start_time"] = self.DEFAULT_WORLD_START_TIME.isoformat()
            run.metadata_json = metadata

        self.session.add_all([plaza, apartment, office, cafe])
        await self.session.flush()
        self.session.add_all([truman, spouse, friend, neighbor])
        await self.session.commit()

    async def _load_world(self, run_id: str, tick_minutes: int) -> WorldState:
        run = await self.run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)
        return await self._context_builder.load_world(run_id, run, tick_minutes)

    def _get_run_world_time(self, run) -> datetime:
        """Calculate current world time from run metadata."""
        from app.sim.context import DEFAULT_WORLD_START_TIME
        from datetime import timedelta

        metadata = run.metadata_json or {}
        raw_start = metadata.get("world_start_time")
        if isinstance(raw_start, str):
            try:
                start_time = datetime.fromisoformat(raw_start)
            except ValueError:
                start_time = DEFAULT_WORLD_START_TIME
        else:
            start_time = DEFAULT_WORLD_START_TIME

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=UTC)

        return start_time + timedelta(minutes=run.current_tick * run.tick_minutes)

    async def _build_director_plan(self, run_id: str, agents: list[Agent]):
        assessment = await self.observe_run(run_id)
        planner = DirectorPlanner()
        return planner.build_plan(assessment=assessment, agents=list(agents))

    def _fallback_intent(
        self,
        agent_id: str,
        current_goal: str | None,
        current_location_id: str,
        home_location_id: str | None,
        nearby_agent_id: str | None,
        world_role: str | None = None,
        current_status: dict | None = None,
        truman_suspicion_score: float = 0.0,
        director_scene_goal: str | None = None,
        director_priority: str | None = None,
    ) -> ActionIntent:
        suspicion_decision = build_suspicion_aware_decision(
            world={
                "world_role": world_role,
                "self_status": current_status or {},
            },
            nearby_agent_id=nearby_agent_id,
            current_location_id=current_location_id,
            home_location_id=home_location_id,
        )
        if suspicion_decision is not None:
            payload = dict(suspicion_decision.payload)
            if suspicion_decision.message:
                payload["message"] = suspicion_decision.message
            return ActionIntent(
                agent_id=agent_id,
                action_type=suspicion_decision.action_type,
                target_location_id=suspicion_decision.target_location_id,
                target_agent_id=suspicion_decision.target_agent_id,
                payload=payload,
            )

        cast_decision = build_cast_stabilizing_decision(
            world={
                "world_role": world_role,
                "truman_suspicion_score": truman_suspicion_score,
                "director_scene_goal": director_scene_goal,
                "director_priority": director_priority,
            },
            nearby_agent_id=nearby_agent_id,
        )
        if cast_decision is not None:
            payload = dict(cast_decision.payload)
            if cast_decision.message:
                payload["message"] = cast_decision.message
            return ActionIntent(
                agent_id=agent_id,
                action_type=cast_decision.action_type,
                target_location_id=cast_decision.target_location_id,
                target_agent_id=cast_decision.target_agent_id,
                payload=payload,
            )

        if isinstance(current_goal, str) and current_goal.startswith("move:"):
            return ActionIntent(
                agent_id=agent_id,
                action_type="move",
                target_location_id=current_goal.split(":", 1)[1].strip(),
            )

        if current_goal == "talk" and nearby_agent_id:
            return ActionIntent(
                agent_id=agent_id,
                action_type="talk",
                target_agent_id=nearby_agent_id,
                payload={"message": build_default_talk_message()},
            )

        if (
            current_goal == "go_home"
            and home_location_id
            and current_location_id != home_location_id
        ):
            return ActionIntent(
                agent_id=agent_id,
                action_type="move",
                target_location_id=home_location_id,
            )

        if current_goal == "work":
            return ActionIntent(agent_id=agent_id, action_type="work")

        return ActionIntent(agent_id=agent_id, action_type="rest")
