from __future__ import annotations

from typing import Literal, TypeAlias

ACTION_MOVE = "move"
ACTION_TALK = "talk"
ACTION_WORK = "work"
ACTION_REST = "rest"

EVENT_MOVE = ACTION_MOVE
EVENT_TALK = ACTION_TALK
EVENT_WORK = ACTION_WORK
EVENT_REST = ACTION_REST
EVENT_PLAN = "plan"
EVENT_REFLECT = "reflect"

DIRECTOR_EVENT_PREFIX = "director_"
DIRECTOR_EVENT_INJECT = f"{DIRECTOR_EVENT_PREFIX}inject"

DIRECTOR_SCENE_SOFT_CHECK_IN = "soft_check_in"
DIRECTOR_SCENE_KEEP_NATURAL = "keep_scene_natural"

ActionType: TypeAlias = Literal[
    "move",
    "talk",
    "work",
    "rest",
    "plan",
    "reflect",
    "director_inject",
]
RejectedActionEventType: TypeAlias = Literal[
    "move_rejected",
    "talk_rejected",
    "work_rejected",
    "rest_rejected",
    "plan_rejected",
    "reflect_rejected",
    "director_inject_rejected",
]
EventType: TypeAlias = ActionType | RejectedActionEventType
DirectorSceneGoal: TypeAlias = Literal["soft_check_in", "keep_scene_natural"]


def build_rejected_event_type(action_type: ActionType) -> RejectedActionEventType:
    return f"{action_type}_rejected"


def build_director_event_type(event_type: str) -> str:
    return f"{DIRECTOR_EVENT_PREFIX}{event_type}"
