import * as Phaser from "phaser";

import type { SceneAgent, SceneLocation, SceneWorld } from "@/lib/world-scene-adapter";

const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const SVG_WIDTH = 700;
const SVG_HEIGHT = 440;
const LOCATION_WIDTH = 88;
const LOCATION_HEIGHT = 58;

type LocationNode = {
  body: Phaser.GameObjects.Rectangle;
  label: Phaser.GameObjects.Text;
  badge: Phaser.GameObjects.Text;
};

type AgentNode = {
  body: Phaser.GameObjects.Arc;
  label: Phaser.GameObjects.Text;
};

function mapSvgToCanvas(x: number, y: number) {
  return {
    x: (x / SVG_WIDTH) * CANVAS_WIDTH,
    y: (y / SVG_HEIGHT) * CANVAS_HEIGHT,
  };
}

function getLocationColor(locationType: string) {
  switch (locationType) {
    case "cafe":
      return 0xf59e0b;
    case "plaza":
      return 0x0ea5e9;
    case "park":
      return 0x10b981;
    case "office":
      return 0x2563eb;
    case "home":
      return 0xec4899;
    default:
      return 0x64748b;
  }
}

function getAgentColor(status: SceneAgent["status"]) {
  switch (status) {
    case "moving":
      return 0x38bdf8;
    case "talking":
      return 0xf97316;
    case "working":
      return 0x22c55e;
    case "resting":
      return 0xa78bfa;
    default:
      return 0xf8fafc;
  }
}

export class WorldScene extends Phaser.Scene {
  private locationNodes = new Map<string, LocationNode>();
  private agentNodes = new Map<string, AgentNode>();
  private currentWorld: SceneWorld | null = null;

  constructor() {
    super({ key: "WorldScene" });
  }

  preload(): void {}

  create(_initialWorld?: SceneWorld): void {
    this.cameras.main.setBackgroundColor("#0f172a");
    this.cameras.main.setZoom(1);

    this.add
      .rectangle(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2, CANVAS_WIDTH, CANVAS_HEIGHT, 0x13233c)
      .setDepth(-20)
      .setAlpha(0.96);

    this.add
      .ellipse(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2, 680, 460, 0x1e293b)
      .setDepth(-19)
      .setAlpha(0.35);
  }

  syncWorld(world: SceneWorld): void {
    this.currentWorld = world;
    this.syncLocations(world.locations);
    this.syncAgents(world.agents, world.locations);
  }

  updateWorldData(world: SceneWorld): void {
    this.syncWorld(world);
  }

  private syncLocations(locations: SceneLocation[]): void {
    const activeIds = new Set(locations.map((location) => location.id));

    for (const [locationId, node] of this.locationNodes.entries()) {
      if (activeIds.has(locationId)) {
        continue;
      }
      node.body.destroy();
      node.label.destroy();
      node.badge.destroy();
      this.locationNodes.delete(locationId);
    }

    for (const location of locations) {
      const point = mapSvgToCanvas(location.x, location.y);
      const existing = this.locationNodes.get(location.id);
      const fillColor = getLocationColor(location.locationType);
      const occupantRatio =
        location.capacity > 0 ? Math.min(location.occupantCount / location.capacity, 1) : 0;
      const alpha = 0.42 + occupantRatio * 0.45;

      if (existing) {
        existing.body.setPosition(point.x, point.y);
        existing.body.setFillStyle(fillColor, alpha);
        existing.label.setPosition(point.x, point.y - 6);
        existing.label.setText(location.name);
        existing.badge.setPosition(point.x, point.y + 12);
        existing.badge.setText(`${location.occupantCount}/${location.capacity}`);
        continue;
      }

      const body = this.add
        .rectangle(point.x, point.y, LOCATION_WIDTH, LOCATION_HEIGHT, fillColor, alpha)
        .setStrokeStyle(2, 0xe2e8f0, 0.75)
        .setDepth(10)
        .setInteractive({ cursor: "pointer" });
      const label = this.add
        .text(point.x, point.y - 6, location.name, {
          color: "#e2e8f0",
          fontFamily: "ui-monospace, SFMono-Regular, monospace",
          fontSize: "12px",
          fontStyle: "600",
        })
        .setOrigin(0.5)
        .setDepth(11);
      const badge = this.add
        .text(point.x, point.y + 12, `${location.occupantCount}/${location.capacity}`, {
          color: "#cbd5e1",
          fontFamily: "ui-monospace, SFMono-Regular, monospace",
          fontSize: "10px",
        })
        .setOrigin(0.5)
        .setDepth(11);

      body.on("pointerdown", () => {
        this.events.emit("location:click", location.id);
      });

      this.locationNodes.set(location.id, { body, label, badge });
    }
  }

  private syncAgents(agents: SceneAgent[], locations: SceneLocation[]): void {
    const locationMap = new Map(locations.map((location) => [location.id, location]));
    const activeIds = new Set(agents.map((agent) => agent.id));

    for (const [agentId, node] of this.agentNodes.entries()) {
      if (activeIds.has(agentId)) {
        continue;
      }
      node.body.destroy();
      node.label.destroy();
      this.agentNodes.delete(agentId);
    }

    for (const agent of agents) {
      const location = locationMap.get(agent.locationId);
      if (!location) {
        continue;
      }

      const point = this.getAgentPosition(location, agent.slotIndex);
      const fillColor = getAgentColor(agent.status);
      const existing = this.agentNodes.get(agent.id);

      if (existing) {
        this.tweens.add({
          targets: existing.body,
          x: point.x,
          y: point.y,
          duration: 260,
          ease: "Quad.Out",
        });
        this.tweens.add({
          targets: existing.label,
          x: point.x,
          y: point.y + 14,
          duration: 260,
          ease: "Quad.Out",
        });
        existing.body.setFillStyle(fillColor, 1);
        existing.label.setText(agent.name);
        continue;
      }

      const body = this.add
        .circle(point.x, point.y, 10, fillColor, 1)
        .setStrokeStyle(2, 0x0f172a, 0.75)
        .setDepth(20)
        .setInteractive({ cursor: "pointer" });
      const label = this.add
        .text(point.x, point.y + 14, agent.name, {
          color: "#f8fafc",
          fontFamily: "ui-monospace, SFMono-Regular, monospace",
          fontSize: "10px",
        })
        .setOrigin(0.5, 0)
        .setDepth(21);

      body.on("pointerdown", () => {
        this.events.emit("agent:click", agent.id);
      });

      this.agentNodes.set(agent.id, { body, label });
    }
  }

  private getAgentPosition(location: SceneLocation, slotIndex: number) {
    const center = mapSvgToCanvas(location.x, location.y);
    const columns = 3;
    const col = slotIndex % columns;
    const row = Math.floor(slotIndex / columns);
    const offsetX = (col - 1) * 18;
    const offsetY = 34 + row * 18;
    return {
      x: center.x + offsetX,
      y: center.y + offsetY,
    };
  }
}
