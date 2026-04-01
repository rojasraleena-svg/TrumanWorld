import { WorldScene } from "../world-scene";

import type { SceneWorld } from "@/lib/world-scene-adapter";

jest.mock("phaser", () => ({
  Scene: class MockScene {
    add = {
      rectangle: jest.fn(() => ({
        setDepth: jest.fn().mockReturnThis(),
        setAlpha: jest.fn().mockReturnThis(),
        setStrokeStyle: jest.fn().mockReturnThis(),
        setInteractive: jest.fn().mockReturnThis(),
        setPosition: jest.fn().mockReturnThis(),
        setFillStyle: jest.fn().mockReturnThis(),
        setScale: jest.fn().mockReturnThis(),
        setSize: jest.fn().mockReturnThis(),
        setVisible: jest.fn().mockReturnThis(),
        on: jest.fn(),
        destroy: jest.fn(),
      })),
      ellipse: jest.fn(() => ({
        setDepth: jest.fn().mockReturnThis(),
        setAlpha: jest.fn().mockReturnThis(),
      })),
      circle: jest.fn(() => ({
        setDepth: jest.fn().mockReturnThis(),
        setStrokeStyle: jest.fn().mockReturnThis(),
        setInteractive: jest.fn().mockReturnThis(),
        setFillStyle: jest.fn().mockReturnThis(),
        setScale: jest.fn().mockReturnThis(),
        setPosition: jest.fn().mockReturnThis(),
        setVisible: jest.fn().mockReturnThis(),
        on: jest.fn(),
        destroy: jest.fn(),
      })),
      line: jest.fn(() => ({
        setOrigin: jest.fn().mockReturnThis(),
        setLineWidth: jest.fn().mockReturnThis(),
        setDepth: jest.fn().mockReturnThis(),
        setTo: jest.fn().mockReturnThis(),
        setAlpha: jest.fn().mockReturnThis(),
        destroy: jest.fn(),
      })),
      triangle: jest.fn(() => ({
        setDepth: jest.fn().mockReturnThis(),
        setRotation: jest.fn().mockReturnThis(),
        setPosition: jest.fn().mockReturnThis(),
        setAlpha: jest.fn().mockReturnThis(),
        setScale: jest.fn().mockReturnThis(),
        destroy: jest.fn(),
      })),
      text: jest.fn(() => ({
        setOrigin: jest.fn().mockReturnThis(),
        setDepth: jest.fn().mockReturnThis(),
        setPosition: jest.fn().mockReturnThis(),
        setText: jest.fn().mockReturnThis(),
        setAlpha: jest.fn().mockReturnThis(),
        setScale: jest.fn().mockReturnThis(),
        setVisible: jest.fn().mockReturnThis(),
        destroy: jest.fn(),
      })),
    };
    cameras = {
      main: {
        setBackgroundColor: jest.fn(),
        setZoom: jest.fn(),
        pan: jest.fn(),
      },
    };
    tweens = {
      add: jest.fn(),
    };
    events = {
      emit: jest.fn(),
    };
    sys = {
      config: { key: "WorldScene" },
    };
  },
  Math: {
    RadToDeg: jest.fn((radians) => radians * (180 / globalThis.Math.PI)),
    DegToRad: jest.fn((degrees) => degrees * (globalThis.Math.PI / 180)),
    Angle: {
      Between: jest.fn(() => 0),
    },
  },
}));

describe("WorldScene", () => {
  const sceneWorld: SceneWorld = {
    runId: "run-1",
    locations: [
      {
        id: "loc-1",
        name: "Cafe",
        locationType: "cafe",
        x: 100,
        y: 120,
        capacity: 6,
        occupantCount: 1,
        heat: 0.5,
      },
    ],
    agents: [
      {
        id: "agent-1",
        name: "Mei",
        locationId: "loc-1",
        status: "talking",
        slotIndex: 0,
      },
    ],
    moveTrails: [
      {
        id: "move-1",
        actorName: "Mei",
        actorId: "agent-1",
        fromLocationId: "loc-1",
        toLocationId: "loc-1",
        recencyIndex: 0,
      },
    ],
    bubbles: [
      {
        id: "bubble-1",
        text: "你好",
        speakerAgentId: "agent-1",
        speakerName: "Mei",
        locationId: "loc-1",
        recencyIndex: 0,
      },
    ],
    ambience: {
      label: "夜晚",
      overlayColor: "rgba(15, 23, 42, 0.35)",
      isDark: true,
    },
  };

  it("creates the scene shell", () => {
    const scene = new WorldScene();
    scene.create();
    expect(scene).toBeDefined();
  });

  it("syncs location and agent nodes", () => {
    const scene = new WorldScene();
    scene.create();
    scene.syncWorld(sceneWorld);
    expect(scene).toBeDefined();
  });
});
