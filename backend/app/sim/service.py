from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.protocol.simulation import build_director_event_type
from app.agent.registry import AgentRegistry
from app.agent.runtime import AgentRuntime
from app.director.manual_planner import ManualDirectorPlanner
from app.director.observer import DirectorAssessment
from app.infra.logging import get_logger
from app.infra.settings import get_settings
from app.scenario.base import Scenario
from app.scenario.factory import create_scenario
from app.scenario.types import (
    get_world_role,
)
from app.sim.action_resolver import ActionIntent
from app.sim.context import ContextBuilder, get_run_world_time
from app.sim.event_utils import build_event
from app.sim.persistence import PersistenceManager
from app.sim.runner import TickResult
from app.sim.tick_orchestrator import TickOrchestrator
from app.sim.tick_persistence import TickPersistenceService
from app.sim.world import WorldState
from app.sim.world_loader import load_tick_data
from app.store.repositories import (
    AgentRepository,
    DirectorMemoryRepository,
    EventRepository,
    LocationRepository,
    RunRepository,
)
from app.store.models import SimulationRun

if TYPE_CHECKING:
    from app.infra.db import async_engine


logger = get_logger(__name__)


class SimulationService:
    """Thin application service coordinating tick orchestration and persistence."""

    def __init__(
        self,
        session: AsyncSession | None,
        agent_runtime: AgentRuntime | None = None,
        agents_root: Path | None = None,
        scenario: Scenario | None = None,
    ) -> None:
        self.session = session
        self.run_repo = RunRepository(session) if session is not None else None
        self.agent_repo = AgentRepository(session) if session is not None else None
        self.location_repo = LocationRepository(session) if session is not None else None
        self.event_repo = EventRepository(session) if session is not None else None
        self.director_memory_repo = (
            DirectorMemoryRepository(session) if session is not None else None
        )
        self._context_builder = ContextBuilder(session) if session is not None else None
        self._persistence = PersistenceManager(session) if session is not None else None
        # Track whether a scenario was explicitly injected (e.g. in tests).
        # When True, run_tick will NOT override _scenario based on run.scenario_type.
        self._injected_scenario: bool = scenario is not None
        self._scenario = (
            scenario.with_session(session)
            if scenario is not None
            else create_scenario("truman_world", session)
        )
        settings = get_settings()
        self.agent_runtime = agent_runtime or AgentRuntime(
            registry=AgentRegistry(agents_root or (settings.project_root / "agents"))
        )
        self._scenario.configure_runtime(self.agent_runtime)

    def _configure_scenario(self, scenario_type: str | None) -> Scenario:
        self._scenario = create_scenario(scenario_type, self.session)
        self._scenario.configure_runtime(self.agent_runtime)
        return self._scenario

    def _configure_scenario_for_run(self, run: SimulationRun) -> Scenario:
        # If a scenario was explicitly injected (e.g. in tests), honour it and
        # do not replace it with a freshly-built one based on run.scenario_type.
        if self._injected_scenario:
            return self._scenario
        return self._configure_scenario(run.scenario_type)

    @classmethod
    def create_for_scheduler(
        cls,
        agent_runtime: AgentRuntime,
        scenario: Scenario | None = None,
    ) -> "SimulationService":
        return cls(
            session=None,
            agent_runtime=agent_runtime,
            scenario=(
                scenario.with_session(None)
                if scenario is not None
                else create_scenario("truman_world")
            ),
        )

    def _require_session_bound(self) -> AsyncSession:
        if self.session is None:
            msg = "SimulationService is not bound to a database session"
            raise RuntimeError(msg)
        return self.session

    def _require_run_repo(self) -> RunRepository:
        if self.run_repo is None:
            msg = "SimulationService requires a bound RunRepository"
            raise RuntimeError(msg)
        return self.run_repo

    def _require_agent_repo(self) -> AgentRepository:
        if self.agent_repo is None:
            msg = "SimulationService requires a bound AgentRepository"
            raise RuntimeError(msg)
        return self.agent_repo

    def _require_event_repo(self) -> EventRepository:
        if self.event_repo is None:
            msg = "SimulationService requires a bound EventRepository"
            raise RuntimeError(msg)
        return self.event_repo

    def _require_context_builder(self) -> ContextBuilder:
        if self._context_builder is None:
            msg = "SimulationService requires a bound ContextBuilder"
            raise RuntimeError(msg)
        return self._context_builder

    def _require_persistence(self) -> PersistenceManager:
        if self._persistence is None:
            msg = "SimulationService requires a bound PersistenceManager"
            raise RuntimeError(msg)
        return self._persistence

    def _build_tick_orchestrator(self) -> TickOrchestrator:
        return TickOrchestrator(
            agent_runtime=self.agent_runtime,
            scenario=self._scenario,
            session=self.session,
            context_builder=self._context_builder,
            agent_repo=self.agent_repo,
        )

    def _build_tick_persistence(self) -> TickPersistenceService:
        return TickPersistenceService(self.session)

    async def run_tick(self, run_id: str, intents: list[ActionIntent] | None = None) -> TickResult:
        run_repo = self._require_run_repo()
        run = await run_repo.get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)
        self._configure_scenario_for_run(run)

        world = await self._load_world(run_id, tick_minutes=run.tick_minutes)
        if not intents:
            intents = await self.prepare_tick_intents(run_id, world)
        result = self._build_tick_orchestrator().execute_tick(
            world=world,
            current_tick=run.current_tick,
            intents=intents,
        )

        await self._require_persistence().persist_agent_locations(run_id, world)
        await run_repo.update_tick(run, result.tick_no)
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
            run = await read_session.get(SimulationRun, run_id)
            if run is None:
                msg = f"Run not found: {run_id}"
                raise ValueError(msg)
            scenario = create_scenario(run.scenario_type, read_session)
            scenario.configure_runtime(self.agent_runtime)
            loaded = await load_tick_data(
                session=read_session,
                run_id=run_id,
                scenario=scenario,
            )
            current_tick = loaded.run.current_tick
            world = loaded.world
            agent_data = loaded.agent_data
            director_plan = loaded.director_plan
        self._scenario = create_scenario(run.scenario_type)
        self._scenario.configure_runtime(self.agent_runtime)
        orchestrator = self._build_tick_orchestrator()

        # Phase 2: Prepare intents (SDK calls happen here, no active session)
        if not intents:
            intents, llm_records = await orchestrator.prepare_intents_from_data(
                world, agent_data, engine, run_id, current_tick
            )
        else:
            llm_records = []

        result = orchestrator.execute_tick(
            world=world,
            current_tick=current_tick,
            intents=intents,
        )
        await TickPersistenceService().persist_isolated_tick(
            run_id=run_id,
            current_tick=current_tick,
            result=result,
            world=world,
            scenario=self._scenario,
            director_plan=director_plan,
            llm_records=llm_records,
            engine=engine,
            agent_runtime=self.agent_runtime,
        )

        return result

    async def _persist_tick_events(self, run_id: str, result: TickResult) -> None:
        await self._build_tick_persistence().persist_tick_events(
            run_id=run_id,
            result=result,
            scenario=self._scenario,
        )

    async def prepare_tick_intents(self, run_id: str, world: WorldState) -> list[ActionIntent]:
        return await self._build_tick_orchestrator().prepare_tick_intents(run_id, world)

    async def inject_director_event(
        self,
        run_id: str,
        event_type: str,
        payload: dict,
        location_id: str | None = None,
        importance: float = 0.5,
    ) -> None:
        """Inject a director event - unified flow via DirectorPlan.

        This method unifies manual injection with automatic intervention
        by converting the event into a DirectorPlan and saving it to
        DirectorMemory, ensuring consistent handling and execution tracking.
        """
        run = await self._require_run_repo().get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)

        # 1. Get all agents and find Truman
        agents = await self._require_agent_repo().list_for_run(run_id)
        truman = next(
            (a for a in agents if get_world_role(a.profile) == "truman"),
            None,
        )

        # 2. Build DirectorPlan from manual event (unified flow)
        manual_planner = ManualDirectorPlanner()
        plan = manual_planner.build_plan_from_manual_event(
            event_type=event_type,
            payload=payload,
            location_id=location_id,
            agents=agents,
            truman_agent_id=truman.id if truman else None,
        )

        if plan is None:
            msg = f"Unsupported director event type: {event_type}"
            raise ValueError(msg)

        # 3. Save to DirectorMemory (unified storage with automatic interventions)
        if self.director_memory_repo is None:
            msg = "SimulationService requires a bound DirectorMemoryRepository"
            raise RuntimeError(msg)
        await self.director_memory_repo.create(
            run_id=run_id,
            tick_no=run.current_tick,
            scene_goal=plan.scene_goal,
            target_cast_ids=plan.target_cast_ids,
            priority=plan.priority,
            urgency=plan.urgency,
            message_hint=plan.message_hint,
            target_agent_id=plan.target_agent_id,
            reason=plan.reason,
            trigger_suspicion_score=0.0,  # Manual injection doesn't depend on suspicion
            trigger_continuity_risk="stable",
            cooldown_ticks=plan.cooldown_ticks,
            location_hint=plan.location_hint,
        )

        # 4. Also create Event for timeline display (optional but useful)
        event = build_event(
            run_id=run_id,
            tick_no=run.current_tick,
            world_time=get_run_world_time(run).isoformat(),
            action_type=build_director_event_type(event_type),
            payload=payload,
            accepted=True,
        )
        event.location_id = location_id
        event.importance = importance
        event.visibility = "system"
        await self._require_event_repo().create(event)

    async def observe_run(self, run_id: str, event_limit: int = 20) -> DirectorAssessment:
        run = await self._require_run_repo().get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)
        self._configure_scenario_for_run(run)
        return await self._scenario.observe_run(run_id, event_limit=event_limit)

    async def seed_demo_run(self, run_id: str) -> None:
        run = await self._require_run_repo().get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)
        self._configure_scenario_for_run(run)

        existing_agents = await self._require_agent_repo().list_for_run(run_id)
        if existing_agents:
            return
        await self._scenario.seed_demo_run(run)

    async def _load_world(self, run_id: str, tick_minutes: int) -> WorldState:
        run = await self._require_run_repo().get(run_id)
        if run is None:
            msg = f"Run not found: {run_id}"
            raise ValueError(msg)
        return await self._require_context_builder().load_world(run_id, run, tick_minutes)
