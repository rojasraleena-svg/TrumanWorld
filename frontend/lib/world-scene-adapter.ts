import { inferAgentStatus, type AgentStatus } from "@/lib/agent-utils";
import { EVENT_MOVE, EVENT_SPEECH, EVENT_TALK } from "@/lib/simulation-protocol";
import type { WorldSnapshot } from "@/lib/types";
import { calculateLocationHeat, buildWorldNameMaps, getTimeOfDay, getTimeOfDayStyle } from "@/lib/world-utils";

export type SceneLocation = {
  id: string;
  name: string;
  locationType: string;
  x: number;
  y: number;
  capacity: number;
  occupantCount: number;
  heat: number;
};

export type SceneAgent = {
  id: string;
  name: string;
  occupation?: string;
  locationId: string;
  status: AgentStatus;
  slotIndex: number;
};

export type SceneMoveTrail = {
  id: string;
  actorName: string;
  fromLocationId: string;
  toLocationId: string;
};

export type SceneBubble = {
  id: string;
  text: string;
  speakerName: string;
  locationId: string;
};

export type SceneWorld = {
  runId: string;
  locations: SceneLocation[];
  agents: SceneAgent[];
  moveTrails: SceneMoveTrail[];
  bubbles: SceneBubble[];
  ambience: {
    label: string;
    overlayColor: string;
    isDark: boolean;
  };
};

export function buildSceneWorld(world: WorldSnapshot): SceneWorld {
  const agents: SceneAgent[] = [];
  const { agentNameMap } = buildWorldNameMaps(world);
  const locationIds = new Set(world.locations.map((location) => location.id));
  const timeOfDay = getTimeOfDay(world.world_clock?.hour ?? 12);
  const timeStyle = getTimeOfDayStyle(timeOfDay);

  for (const location of world.locations) {
    location.occupants
      .slice()
      .sort((left, right) => left.id.localeCompare(right.id))
      .forEach((agent, index) => {
        agents.push({
          id: agent.id,
          name: agent.name,
          occupation: agent.occupation,
          locationId: location.id,
          status: inferAgentStatus(agent.id, world.recent_events),
          slotIndex: index,
        });
      });
  }

  return {
    runId: world.run.id,
    locations: world.locations.map((location) => ({
      id: location.id,
      name: location.name,
      locationType: location.location_type,
      x: location.x,
      y: location.y,
      capacity: location.capacity,
      occupantCount: location.occupants.length,
      heat: calculateLocationHeat(location.id, world.recent_events),
    })),
    agents,
    moveTrails: world.recent_events
      .filter((event) => event.event_type === EVENT_MOVE)
      .slice(0, 4)
      .map((event) => {
        const fromLocationId = String(event.payload.from_location_id ?? "");
        const toLocationId = String(event.payload.to_location_id ?? event.location_id ?? "");
        return {
          id: event.id,
          actorName:
            agentNameMap[event.actor_agent_id ?? ""] ?? event.actor_name ?? event.actor_agent_id ?? "某人",
          fromLocationId,
          toLocationId,
        };
      })
      .filter(
        (trail) => locationIds.has(trail.fromLocationId) && locationIds.has(trail.toLocationId)
      ),
    bubbles: world.recent_events
      .filter((event) => event.event_type === EVENT_SPEECH || event.event_type === EVENT_TALK)
      .slice(0, 3)
      .map((event) => {
        const text = String(event.payload.message ?? "").trim();
        const locationId = String(event.location_id ?? "");
        return {
          id: event.id,
          text: text.length > 22 ? `${text.slice(0, 22)}...` : text,
          speakerName:
            agentNameMap[event.actor_agent_id ?? ""] ?? event.actor_name ?? event.actor_agent_id ?? "某人",
          locationId,
        };
      })
      .filter((bubble) => bubble.text.length > 0 && locationIds.has(bubble.locationId)),
    ambience: {
      label: timeStyle.label,
      overlayColor: timeStyle.overlayColor,
      isDark: timeStyle.isDark,
    },
  };
}
