export const ACTION_MOVE = "move";
export const ACTION_TALK = "talk";
export const ACTION_WORK = "work";
export const ACTION_REST = "rest";

export const EVENT_MOVE = ACTION_MOVE;
export const EVENT_TALK = ACTION_TALK;
export const EVENT_WORK = ACTION_WORK;
export const EVENT_REST = ACTION_REST;
export const EVENT_PLAN = "plan";
export const EVENT_REFLECT = "reflect";

export const DIRECTOR_EVENT_PREFIX = "director_";
export const DIRECTOR_EVENT_INJECT = `${DIRECTOR_EVENT_PREFIX}inject`;

export const DIRECTOR_SCENE_SOFT_CHECK_IN = "soft_check_in";
export const DIRECTOR_SCENE_KEEP_NATURAL = "keep_scene_natural";

export type ActionType =
  | typeof ACTION_MOVE
  | typeof ACTION_TALK
  | typeof ACTION_WORK
  | typeof ACTION_REST
  | typeof EVENT_PLAN
  | typeof EVENT_REFLECT
  | typeof DIRECTOR_EVENT_INJECT;

export type RejectedActionEventType =
  | `${typeof ACTION_MOVE}_rejected`
  | `${typeof ACTION_TALK}_rejected`
  | `${typeof ACTION_WORK}_rejected`
  | `${typeof ACTION_REST}_rejected`
  | `${typeof EVENT_PLAN}_rejected`
  | `${typeof EVENT_REFLECT}_rejected`
  | `${typeof DIRECTOR_EVENT_INJECT}_rejected`;

export type EventType = ActionType | RejectedActionEventType;

export type DirectorSceneGoal =
  | typeof DIRECTOR_SCENE_SOFT_CHECK_IN
  | typeof DIRECTOR_SCENE_KEEP_NATURAL;
