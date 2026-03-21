from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.sim.action_resolver import ActionIntent, ActionResolver, ActionResult
from app.sim.conversation_scheduler import (
    ConversationAssignment,
    ConversationScheduler,
    ConversationSession,
)
from app.sim.governance_consequences import (
    apply_governance_attention_decay,
    apply_governance_consequences,
)
from app.sim.world import ActiveConversationState, WorldState


@dataclass
class TickResult:
    tick_no: int
    world_time: str
    tick_delta: int
    accepted: list[ActionResult]
    rejected: list[ActionResult]


class SimulationRunner:
    """Coordinates simulation ticks for a run."""

    def __init__(self, world: WorldState, resolver: ActionResolver | None = None) -> None:
        self.world = world
        self.resolver = resolver or ActionResolver()
        self.conversation_scheduler = ConversationScheduler()
        self.tick_no = 0

    def tick(self, intents: Iterable[ActionIntent]) -> TickResult:
        accepted: list[ActionResult] = []
        rejected: list[ActionResult] = []
        previous_day_index = self.world.current_time.toordinal()
        policy_values = self._policy_values()

        intent_list = list(intents)
        self.resolver.reset_tick()
        sessions, assignments = self.conversation_scheduler.schedule(intent_list, self.world)
        participants_by_conversation_id = {
            session.id: list(session.participant_ids) for session in sessions
        }
        conversation_assignments = {
            assignment.agent_id: {
                "role": assignment.role,
                "conversation_id": assignment.conversation_id,
                "participant_ids": participants_by_conversation_id.get(
                    assignment.conversation_id, []
                ),
            }
            for assignment in assignments.values()
        }
        self.resolver.prefill_conversation_assignments(conversation_assignments)
        accepted.extend(self._build_conversation_structure_results(sessions, assignments))
        for intent in intent_list:
            if self._should_skip_intent(intent, assignments):
                continue
            result = self.resolver.resolve(self.world, intent)
            apply_governance_consequences(self.world, result, policy_values=policy_values)
            if result.accepted:
                accepted.append(result)
            else:
                rejected.append(result)
        accepted.extend(self._build_listen_results(sessions, assignments))

        advanced = self.world.advance_tick()
        self._store_active_conversations(
            sessions,
            accepted=accepted,
            tick_no=self.tick_no + advanced.tick_delta,
        )
        days_elapsed = advanced.current_time.toordinal() - previous_day_index
        apply_governance_attention_decay(
            self.world,
            days_elapsed=days_elapsed,
            policy_values=policy_values,
        )
        world_time = advanced.current_time.isoformat()
        self.tick_no += advanced.tick_delta
        return TickResult(
            tick_no=self.tick_no,
            world_time=world_time,
            tick_delta=advanced.tick_delta,
            accepted=accepted,
            rejected=rejected,
        )

    def _policy_values(self) -> dict[str, object]:
        package = getattr(self.resolver, "_world_design_package", None)
        if package is None:
            return {}
        return dict((package.policy_config.values or {}))

    @staticmethod
    def _should_skip_intent(
        intent: ActionIntent,
        assignments: dict[str, ConversationAssignment],
    ) -> bool:
        assignment = assignments.get(intent.agent_id)
        if assignment is None:
            return False
        # A joiner already produces conversation_joined + listen events.
        # Re-processing the original talk intent would turn a successful join
        # into a synthetic talk_rejected, which pollutes rejection metrics.
        return intent.action_type == "talk" and assignment.reason in {
            "conversation_joiner",
            "reciprocal_talk_listener",
        }

    def _build_conversation_structure_results(
        self,
        sessions: list[ConversationSession],
        assignments: dict[str, ConversationAssignment],
    ) -> list[ActionResult]:
        structure_results: list[ActionResult] = []

        for session in sessions:
            if not session.is_new:
                continue
            primary_listener_id = next(
                (
                    participant_id
                    for participant_id in session.participant_ids
                    if participant_id != session.active_speaker_id
                ),
                None,
            )
            structure_results.append(
                ActionResult(
                    accepted=True,
                    action_type="conversation_started",
                    reason="accepted",
                    event_payload={
                        "agent_id": session.active_speaker_id,
                        "target_agent_id": primary_listener_id,
                        "location_id": session.location_id,
                        "conversation_id": session.id,
                        "conversation_event_type": "conversation_started",
                        "speaker_agent_id": session.active_speaker_id,
                        "participant_ids": list(session.participant_ids),
                    },
                )
            )

        session_by_id = {session.id: session for session in sessions}
        for assignment in assignments.values():
            if assignment.reason != "conversation_joiner" or assignment.conversation_id is None:
                continue
            session = session_by_id.get(assignment.conversation_id)
            if session is None:
                continue
            structure_results.append(
                ActionResult(
                    accepted=True,
                    action_type="conversation_joined",
                    reason="accepted",
                    event_payload={
                        "agent_id": assignment.agent_id,
                        "target_agent_id": session.active_speaker_id,
                        "location_id": session.location_id,
                        "conversation_id": session.id,
                        "conversation_event_type": "conversation_joined",
                        "speaker_agent_id": session.active_speaker_id,
                        "participant_ids": list(session.participant_ids),
                    },
                )
            )

        return structure_results

    def _build_listen_results(
        self,
        sessions: list[ConversationSession],
        assignments: dict[str, ConversationAssignment],
    ) -> list[ActionResult]:
        session_by_id = {session.id: session for session in sessions}
        listen_results: list[ActionResult] = []

        for assignment in assignments.values():
            if assignment.role != "listener" or assignment.conversation_id is None:
                continue

            session = session_by_id.get(assignment.conversation_id)
            if session is None:
                continue

            listen_results.append(
                ActionResult(
                    accepted=True,
                    action_type="listen",
                    reason="accepted",
                    event_payload={
                        "agent_id": assignment.agent_id,
                        "target_agent_id": session.active_speaker_id,
                        "location_id": session.location_id,
                        "conversation_id": session.id,
                        "conversation_role": "listener",
                        "conversation_event_type": "listen",
                        "speaker_agent_id": session.active_speaker_id,
                        "participant_ids": list(session.participant_ids),
                    },
                )
            )

        return listen_results

    def _store_active_conversations(
        self,
        sessions: list[ConversationSession],
        *,
        accepted: list[ActionResult],
        tick_no: int,
    ) -> None:
        accepted_speeches_by_conversation_id = {
            item.event_payload["conversation_id"]: item
            for item in accepted
            if item.action_type == "talk" and isinstance(item.event_payload.get("conversation_id"), str)
        }
        self.world.active_conversations = {
            session.id: ActiveConversationState(
                id=session.id,
                location_id=session.location_id,
                participant_ids=list(session.participant_ids),
                active_speaker_id=session.active_speaker_id,
                last_tick_no=tick_no,
                last_message_summary=self._conversation_message_for_session(
                    session.id,
                    accepted_speeches_by_conversation_id,
                    "message",
                ),
                last_proposal=self._conversation_last_proposal_for_session(
                    session.id,
                    accepted_speeches_by_conversation_id,
                ),
                open_question=self._conversation_open_question_for_session(
                    session.id,
                    accepted_speeches_by_conversation_id,
                ),
                repeat_count=self._conversation_repeat_count_for_session(
                    session.id,
                    accepted_speeches_by_conversation_id,
                ),
            )
            for session in sessions
        }

    def _conversation_message_for_session(
        self,
        conversation_id: str,
        accepted_speeches_by_conversation_id: dict[str, ActionResult],
        key: str,
    ) -> str | None:
        speech = accepted_speeches_by_conversation_id.get(conversation_id)
        if speech is None:
            previous = self.world.active_conversations.get(conversation_id)
            return getattr(previous, key, None) if previous is not None else None
        value = speech.event_payload.get("message")
        return value if isinstance(value, str) and value.strip() else None

    def _conversation_last_proposal_for_session(
        self,
        conversation_id: str,
        accepted_speeches_by_conversation_id: dict[str, ActionResult],
    ) -> str | None:
        message = self._conversation_message_for_session(
            conversation_id,
            accepted_speeches_by_conversation_id,
            "last_proposal",
        )
        if message and self._looks_like_proposal_or_question(message):
            return message
        previous = self.world.active_conversations.get(conversation_id)
        return previous.last_proposal if previous is not None else None

    def _conversation_open_question_for_session(
        self,
        conversation_id: str,
        accepted_speeches_by_conversation_id: dict[str, ActionResult],
    ) -> str | None:
        message = self._conversation_message_for_session(
            conversation_id,
            accepted_speeches_by_conversation_id,
            "open_question",
        )
        if message and self._looks_like_question(message):
            return message
        return None

    def _conversation_repeat_count_for_session(
        self,
        conversation_id: str,
        accepted_speeches_by_conversation_id: dict[str, ActionResult],
    ) -> int:
        speech = accepted_speeches_by_conversation_id.get(conversation_id)
        previous = self.world.active_conversations.get(conversation_id)
        if speech is None:
            return previous.repeat_count if previous is not None else 0

        message = speech.event_payload.get("message")
        if not isinstance(message, str) or not message.strip():
            return 0
        normalized_message = self._normalize_conversation_text(message)
        previous_message = previous.last_proposal if previous is not None else None
        if isinstance(previous_message, str) and self._normalize_conversation_text(previous_message) == normalized_message:
            return (previous.repeat_count if previous is not None else 1) + 1
        return 1

    @staticmethod
    def _normalize_conversation_text(text: str) -> str:
        return "".join(text.split()).strip("，。！？,.!?：:;；\"'“”‘’").lower()

    @staticmethod
    def _looks_like_question(message: str) -> bool:
        return any(token in message for token in ("？", "?", "要不要", "可以吗", "方便吗", "吗"))

    @staticmethod
    def _looks_like_proposal_or_question(message: str) -> bool:
        return SimulationRunner._looks_like_question(message) or any(
            token in message for token in ("一起", "先花十分钟", "要不", "不如")
        )
