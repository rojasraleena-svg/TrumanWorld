# Agents

本目录现在只保留模板与兼容说明，不再承载实际场景运行角色。

## 结构

```text
agents/
  _template/
    agent.yml
    prompt.md
```

实际运行中的角色应放在对应场景包内：

```text
scenarios/
  truman_world/
    agents/
      alice/
        agent.yml
        prompt.md
```

运行时 agent 通过场景包根目录解析配置。当前 Truman world 的真源目录是
`scenarios/truman_world/agents/`。

## Prompt 分层

- `backend/app/agent/system_prompt.py` 负责全局规则，例如语言、世界约束、输出边界。
- `scenarios/<scenario_id>/agents/*/prompt.md` 只负责角色身份、行为风格和个体差异。
- 新增 agent 时，不要在 `prompt.md` 中重复写全局规则，避免规则漂移。

## 模板用途

`agents/_template/` 仍保留为快速创建新 agent 的最小模板。
