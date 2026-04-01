import * as Phaser from "phaser";

import type { SceneAgent, SceneLocation, SceneWorld } from "@/lib/world-scene-adapter";
import { getHeatLevel } from "@/lib/world-utils";

const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const SVG_WIDTH = 700;
const SVG_HEIGHT = 440;
const LOCATION_WIDTH = 88;
const LOCATION_HEIGHT = 58;

type LocationNode = {
  glow: Phaser.GameObjects.Arc;
  body: Phaser.GameObjects.Rectangle;
  label: Phaser.GameObjects.Text;
  badge: Phaser.GameObjects.Text;
};

type AgentNode = {
  body: Phaser.GameObjects.Arc;
  label: Phaser.GameObjects.Text;
};

type TrailNode = {
  line: Phaser.GameObjects.Line;
  label: Phaser.GameObjects.Text;
};

type BubbleNode = {
  box: Phaser.GameObjects.Rectangle;
  text: Phaser.GameObjects.Text;
};

function mapSvgToCanvas(x: number, y: number) {
  return {
    x: (x / SVG_WIDTH) * CANVAS_WIDTH,
    y: (y / SVG_HEIGHT) * CANVAS_HEIGHT,
  };
}

function parseRgbaColor(input: string): number {
  const match = input.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
  if (!match) {
    return 0xffffff;
  }
  const [, r, g, b] = match;
  return (Number(r) << 16) + (Number(g) << 8) + Number(b);
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
  private trailNodes = new Map<string, TrailNode>();
  private bubbleNodes = new Map<string, BubbleNode>();
  private ambienceOverlay: Phaser.GameObjects.Rectangle | null = null;
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

    this.ambienceOverlay = this.add
      .rectangle(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2, CANVAS_WIDTH, CANVAS_HEIGHT, 0xffffff)
      .setDepth(-18)
      .setAlpha(0);
  }

  syncWorld(world: SceneWorld): void {
    this.currentWorld = world;
    this.syncAmbience(world);
    this.syncLocations(world.locations);
    this.syncAgents(world.agents, world.locations);
    this.syncMoveTrails(world);
    this.syncBubbles(world);
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
      node.glow.destroy();
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
      const heatLevel = getHeatLevel(location.heat);

      if (existing) {
        existing.glow.setPosition(point.x, point.y);
        existing.glow.setScale((38 + location.heat * 18) / 38);
        existing.glow.setFillStyle(
          Number.parseInt(heatLevel.color.replace("#", ""), 16),
          0.08 + location.heat * 0.22
        );
        existing.body.setPosition(point.x, point.y);
        existing.body.setFillStyle(fillColor, alpha);
        existing.label.setPosition(point.x, point.y - 6);
        existing.label.setText(location.name);
        existing.badge.setPosition(point.x, point.y + 12);
        existing.badge.setText(`${location.occupantCount}/${location.capacity}`);
        continue;
      }

      const glow = this.add
        .circle(point.x, point.y, 38 + location.heat * 18, Number.parseInt(heatLevel.color.replace("#", ""), 16), 0.08 + location.heat * 0.22)
        .setDepth(8);
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

      this.locationNodes.set(location.id, { glow, body, label, badge });
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

  private syncMoveTrails(world: SceneWorld): void {
    const activeIds = new Set(world.moveTrails.map((trail) => trail.id));
    const locationMap = new Map(world.locations.map((location) => [location.id, location]));

    for (const [trailId, node] of this.trailNodes.entries()) {
      if (activeIds.has(trailId)) {
        continue;
      }
      node.line.destroy();
      node.label.destroy();
      this.trailNodes.delete(trailId);
    }

    for (const trail of world.moveTrails) {
      const fromLocation = locationMap.get(trail.fromLocationId);
      const toLocation = locationMap.get(trail.toLocationId);
      if (!fromLocation || !toLocation) {
        continue;
      }

      const fromPoint = mapSvgToCanvas(fromLocation.x, fromLocation.y);
      const toPoint = mapSvgToCanvas(toLocation.x, toLocation.y);
      const midX = (fromPoint.x + toPoint.x) / 2;
      const midY = (fromPoint.y + toPoint.y) / 2 - 18;
      const existing = this.trailNodes.get(trail.id);

      if (existing) {
        existing.line.setTo(fromPoint.x, fromPoint.y, toPoint.x, toPoint.y);
        existing.label.setPosition(midX, midY);
        existing.label.setText(`${trail.actorName} →`);
        continue;
      }

      const line = this.add
        .line(0, 0, fromPoint.x, fromPoint.y, toPoint.x, toPoint.y, 0x38bdf8, 0.55)
        .setOrigin(0, 0)
        .setLineWidth(2, 2)
        .setDepth(14);
      const label = this.add
        .text(midX, midY, `${trail.actorName} →`, {
          color: "#7dd3fc",
          fontFamily: "ui-monospace, SFMono-Regular, monospace",
          fontSize: "10px",
        })
        .setOrigin(0.5)
        .setDepth(15);

      this.trailNodes.set(trail.id, { line, label });
    }
  }

  private syncBubbles(world: SceneWorld): void {
    const activeIds = new Set(world.bubbles.map((bubble) => bubble.id));
    const locationMap = new Map(world.locations.map((location) => [location.id, location]));

    for (const [bubbleId, node] of this.bubbleNodes.entries()) {
      if (activeIds.has(bubbleId)) {
        continue;
      }
      node.box.destroy();
      node.text.destroy();
      this.bubbleNodes.delete(bubbleId);
    }

    for (const bubble of world.bubbles) {
      const location = locationMap.get(bubble.locationId);
      if (!location) {
        continue;
      }

      const point = mapSvgToCanvas(location.x, location.y);
      const bubbleY = point.y - 58;
      const textValue = `${bubble.speakerName}: ${bubble.text}`;
      const existing = this.bubbleNodes.get(bubble.id);

      if (existing) {
        existing.box.setPosition(point.x, bubbleY);
        existing.text.setPosition(point.x, bubbleY);
        existing.text.setText(textValue);
        continue;
      }

      const box = this.add
        .rectangle(point.x, bubbleY, 150, 28, 0xf8fafc, 0.92)
        .setStrokeStyle(1, 0xcbd5e1, 0.9)
        .setDepth(30);
      const text = this.add
        .text(point.x, bubbleY, textValue, {
          color: "#0f172a",
          fontFamily: "ui-monospace, SFMono-Regular, monospace",
          fontSize: "10px",
        })
        .setOrigin(0.5)
        .setDepth(31);

      this.bubbleNodes.set(bubble.id, { box, text });
    }
  }

  private syncAmbience(world: SceneWorld): void {
    if (!this.ambienceOverlay) {
      return;
    }

    this.ambienceOverlay.setFillStyle(
      parseRgbaColor(world.ambience.overlayColor),
      world.ambience.isDark ? 0.24 : 0.1
    );
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
