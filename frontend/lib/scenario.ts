export function formatScenarioLabel(scenarioType?: string | null): string {
  if (!scenarioType) {
    return "未知世界";
  }

  return scenarioType
    .split("_")
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}
