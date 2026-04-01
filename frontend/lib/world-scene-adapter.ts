import { inferAgentStatus, type AgentStatus } from "@/lib/agent-utils";
import type { WorldSnapshot } from "@/lib/types";

export type SceneLocation = {
  id: string;
  name: string;
  locationType: string;
  x: number;
  y: number;
  capacity: number;
  occupantCount: number;
};

export type SceneAgent = {
  id: string;
  name: string;
  occupation?: string;
  locationId: string;
  status: AgentStatus;
  slotIndex: number;
};

export type SceneWorld = {
  runId: string;
  locations: SceneLocation[];
  agents: SceneAgent[];
};

export function buildSceneWorld(world: WorldSnapshot): SceneWorld {
  const agents: SceneAgent[] = [];

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
    })),
    agents,
  };
}
