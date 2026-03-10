# 每日规划任务

现在是新的一天的开始。作为 {agent_name}，你需要为今天制定一份合理的日程计划。

## 任务要求

基于你的角色身份、个性特点、昨日经历，以及当前的世界状态，规划今天的活动安排。

- 计划需要符合你的职业和生活节奏
- 如果昨天有未完成的心愿或约定，可以纳入今天的计划
- 计划要真实自然，不要过于完美或戏剧化

## 输出格式

只返回一个 JSON 对象，包含以下字段：

```json
{
  "morning": "wander | work | talk | rest | commute",
  "daytime": "wander | work | talk | rest | commute",
  "evening": "socialize | work | rest | go_home",
  "intention": "一句话说明今天最想做的事（30字以内）"
}
```

- `morning` / `daytime` / `evening` 必须从括号内的值中选一个
- `intention` 是自然语言，用第一人称表达
- 只返回 JSON，不要有任何其他文字
