import { getEventExplanations } from "@/lib/event-utils";

describe("getEventExplanations", () => {
  it("returns relationship impact summary and soft risk reason", () => {
    const explanations = getEventExplanations({
      payload: {
        relationship_impact: {
          summary: "高风险社交接触降低了信任和亲近感的增长。",
        },
        rule_evaluation: {
          decision: "soft_risk",
          reason: "late_night_talk_risk",
        },
      },
    });

    expect(explanations).toEqual([
      {
        kind: "relationship",
        text: "高风险社交接触降低了信任和亲近感的增长。",
        tone: "rose",
      },
      {
        kind: "risk",
        text: "深夜社交风险",
        tone: "amber",
      },
    ]);
  });

  it("returns empty list when payload has no explanation metadata", () => {
    const explanations = getEventExplanations({ payload: {} });
    expect(explanations).toEqual([]);
  });
});
