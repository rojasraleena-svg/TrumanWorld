# World Design Implementation Roadmap

- 类型：`engineering`
- 状态：`draft`
- 负责人：`repo`
- 基线日期：`2026-03-21`

## 1. 总体策略

不直接重写 `sim` 主链路。

先做制度资产层，再做最小规则裁决层，最后补治理执行层和解释链。

当前实现状态：

- 已完成阶段 1、阶段 2、阶段 3 的最小可用版本
- 已完成阶段 4 的最小可用版本
- 已完成治理后果层的最小可用版本
- 已补上解释链的最小暴露路径：timeline `rule_evaluation / governance_execution`、agent context `world_rules_summary`
- 已补上 agent detail API 与 director console 对 `world_rules_summary` 的最小展示链路
- 已补上会话连续性状态在 runtime context 中的最小暴露，并增加重复提议保护
- 已补上规则反馈写入长期记忆的最小闭环
- 已补上独立治理记录模型 `governance_records`
- 已补上 agent API 与 director API 对治理历史的查询能力
- 已补上 director console 对治理历史的最小运营视图
- 已补上基于 `observation_count / warning_count` 的再犯升级逻辑
- 阶段 5 关系后果层已进入最小实现阶段
- 阶段 6 心智模型层已完成文档设计，待启动实施

当前明确边界：

- 当前世界已具备“规则可见化 + 选择性治理 + 治理留痕 + 再犯升级 + director 运营可见性”
- 当前世界仍未进入“机构化社会治理”阶段
- 当前 agent 仍然没有独立资产、库存、所有权、收入或罚款账户模型

## 2. 推荐阶段

### 阶段 1：资产层落位

状态：`已完成（最小版）`

目标：

- 在 bundle 中新增 `constitution.md`
- 在 bundle 中新增 `rules.yml`
- 在 bundle 中新增 `policies/default.yml`
- 扩展 loader，支持读取完整 world design 资产包

这个阶段重点不是 evaluator，而是 schema 与边界。

当前已落地：

- `bundle_registry.py` 已支持读取 `rules.yml`、`policies/default.yml`、`constitution.md`
- `backend/app/scenario/runtime/world_design.py` 已装配统一 `WorldDesignRuntimePackage`
- `rules.yml` 缺失时回退为空规则集
- `policies/default.yml` 缺失时回退到平台默认 policy 值
- `constitution.md` 缺失时回退为空文本

### 阶段 2：统一 facts

状态：`已完成（最小版）`

目标：

- 定义平台 facts 命名空间
- 让 `rules.yml` 只引用统一 facts
- 避免规则资产直接耦合 Python 字段名

第一版建议支持：

- `actor.*`
- `target_agent.*`
- `target_location.*`
- `world.*`
- `policy.*`

当前已落地：

- 已有 `fact_resolver.py`
- 规则评估不再直接耦合零散 Python 字段名
- 当前 facts 主要覆盖 actor / target_agent / target_location / world / policy 几个基础域
- 仍未形成独立文档化 schema 校验器，属于运行时约定

### 阶段 3：最小规则裁决层

状态：`已完成（最小版）`

目标：

- 在动作进入 `ActionResolver` 前做规则评估
- 输出结构化裁决结果
- 不推翻现有物理校验和基础执行逻辑

第一版只需要支持少量规则模板和条件操作符。

当前已落地：

- 已有 `rule_evaluator.py`
- 当前支持按 `action_types` 触发、按事实条件匹配、按 `priority + decision` 排序裁决
- 当前决策类型为 `allowed / soft_risk / violates_rule / impossible`
- `soft_risk` 允许动作继续执行，但会附带解释结果
- `RuleEvaluationResult` 已可输出 `matched_tags`
- 这是最小实现，不代表最终治理语义

### 阶段 4：治理执行层

状态：`已完成（最小版）`

目标：

- 根据 `violates_rule` 或高风险裁决，决定是否观察到、是否介入
- 把执行强度主要交给 `policies/*.yml`
- 记录执行事件和长期状态变化

第一阶段不必实现完整政府组织模拟。

当前已落地：

- 已有 `governance_executor.py`
- 当前把 `rule_evaluation` 映射为 `allow / warn / block / record_only`
- `impossible` 当前固定映射为 `block`
- `soft_risk` 当前默认映射为 `warn`
- `violates_rule` 当前会根据 `inspection_level` 和命中的治理信号决定 `warn` 或 `block`
- `subject` / `sensitive_location` 等信号会把治理结果提升为更严格处置
- accepted / rejected event payload 已可附带 `governance_execution`
- agent context 已可读取最近 `block / warn` 结果形成轻量反馈

当前明确未实现：

- 执法 agent
- 更完整的程序层治理（申诉、复核、豁免、差别权限）
- 更细的长期处罚与跨机构协同
- 政府或治理 agent
- 更细的 policy overlay 与运行时动态调度

下一步建议顺序：

1. 先继续维持无执法 agent 的平台级治理语义
2. 把执行语义逐步抽成可替换的 enforcement provider 接口
3. 在 director 运营视图稳定后，再评估是否引入执法 agent

### 阶段 4.5：治理后果层

状态：`已完成（最小版）`

目标：

- 把 `warn / block` 写入 agent 的长期状态
- 让治理执行真正形成跨 tick 的制度记忆
- 为 `current_risks` 和后续治理升级提供稳定输入

当前已落地：

- 已有 `governance_consequences.py`
- 当前会把 `warn / block` 写回 actor 自身的运行时 `status`
- 当前已落地的状态字段包括 `observation_count`、`warning_count` 与 `governance_attention_score`
- `warn` 与 `block` 会通过 policy 参数以不同强度提升 `governance_attention_score`
- `governance_attention_score` 已支持按天衰减
- `governance_attention_score` 已开始驱动 agent context 中的 `current_risks`
- 显著的 `warn / block` 当前也已写入 agent 长期记忆
- `record_only / warn / block` 当前都已进入独立 `governance_records` ledger
- `governance_records` 当前已可从 agent API 与 director API 查询
- director console 当前已可查看治理历史并按决策类型过滤
- 再犯升级当前已开始读取 `observation_count / warning_count`

当前明确未实现：

- 治理后果对 relationship / reputation / economy 的外溢
- 更复杂的恢复机制与多因子衰减
- 跨机构治理后果与程序性治理状态

### 阶段 5：关系后果层

状态：`已完成（最小版）`

目标：

- 把 relationship 明确归入后果层，而不是继续散落在持久化细节中
- 让关系更新读取规则裁决结果与 `policy` 上下文
- 支持正向、负向和时间衰减三类变化
- 在 perception / prompt / API 中暴露派生后的 `relationship_level`

这一阶段重点不是做复杂社交图，而是让“关系为什么变化”可解释、可调参、可与场景一致。

当前已落地：

- relationship delta 已会读取 `rule_evaluation`
- relationship delta 已会读取 `governance_execution`
- relationship delta 已开始读取 actor / target 的 `governance_attention_score`
- `relationship_impact` payload 已可附带 `governance_decision / governance_reason`
- 高 attention 状态已经会进一步削弱 trust / affinity 增长

当前明确未实现：

- relationship 增量参数的 policy 化
- relationship 对 reputation / memory / director 的联动
- 更复杂的双边非对称后果模型

### 阶段 6：心智模型层

状态：`待启动`

目标：

- 为 Agent 增加结构化的心理状态
- 支撑更类人的行为决策
- 为认知模拟实验（如观点极化、信息传播）提供基础

文档：`MENTAL_STATE_MODEL.md`

三层结构：

- 情感层（Emotions）：即时情绪反应， valence/arousal + 基础情绪
- 需求层（Needs）：马斯洛需求层次，动态追踪满足度
- 认知层（Cognition）：社会态度、信念、价值观（后续阶段）

建议实施顺序：

- Phase 6.1（1-2周）：情感层基础版
  - 定义 EmotionalState 类
  - 事件 → 情感 更新规则
  - 情感 → 行为倾向影响（prompt 注入）
  - 与 World Rules Summary 集成
- Phase 6.2（2周）：需求层基础版
  - 定义 NeedState 类
  - Tick 自然衰减机制
  - 需求 → 行为优先级影响
- Phase 6.3（2-3周，可选）：认知层基础版
  - 定义 CognitionState 类
  - 社会议题态度建模
  - 信息接触 → 认知更新

当前明确不做：

- 复杂情感计算模型（如多因子情感交互）
- 全面认知图谱
- 群体心智（集体情绪、群体极化）

第一阶段与现有组件的交互：

- 心智状态 → 影响 Relationship 演化方向
- 心智状态 → 影响 Memory 编码权重
- 心智状态 → 影响 Agent Visible Summary
- 心智状态 → 影响 Planner/Reactor 决策

## 3. 当前仓库的建议切入点

### 3.1 Bundle 侧

- 扩展 `backend/app/scenario/bundle_registry.py`
- 增加对 `rules.yml`、`constitution.md`、`policies/` 的加载能力

### 3.2 Runtime 侧

- 在 `backend/app/scenario/runtime/` 下增加 world design 运行时装配
- 把散落的 world design 配置收敛成一个 package

### 3.3 Simulation 侧

- 在 `backend/app/sim/` 下引入最小 rule evaluation
- 保留 `ActionResolver` 的底层执行职责
- 后续再补治理执行器
- 不再把 relationship 演化语义只写在持久化提交逻辑里

### 3.4 API / Timeline 侧

- 在 event payload 中增加规则解释信息
- 后续统一暴露到 timeline / agent detail

当前已落地：

- rejected / accepted event payload 已可附带 `rule_evaluation`
- rejected / accepted event payload 已可附带 `governance_execution`
- timeline payload 已可透传 `rule_evaluation / governance_execution`
- agent detail API 已可透传 `world_rules_summary`
- agent governance records API 已可透传治理 ledger
- director governance records API 已可透传 run 级治理 ledger
- director console 已有治理历史最小视图

## 4. 当前完成度判断

如果按“像不像一个真实社会治理系统”来衡量，当前大致处于：

- 已经不只是规则校验器
- 已经是一个有观察、留痕、升级、解释和运营视图的最小治理系统
- 但仍远未达到真实社会治理中的机构层、程序层和经济层

目前已经能表达：

- 同样的违规不一定每次都被同等处理
- 治理结果会跨 tick 留痕
- 累犯会提高后续被观察和被介入的概率
- 导演可以从个人与 run 两个视角追踪治理历史

目前还不能表达：

- 谁在执法、谁有权限、谁负责复核
- 罚款、停业、资产冻结、配给限制等经济性后果
- 机构之间的分工与治理冲突

结论：

- 当前 agent 没有自己的资产
- 当前 agent 没有真实所有权与可结算账户
- 当前治理更接近“叙事世界中的平台级秩序维护”，而不是“完整社会治理仿真”
- context event formatting 已补 `rule_feedback_reason / governance_feedback_reason`
- agent detail API 已返回 `world_rules_summary`
- 前端 agent detail 共享面板已展示 `world_rules_summary`

### 3.4.1 Agent 学习闭环补充

- `governance_execution.reason` 当前会写入长期记忆
- 纯 `rule_evaluation.reason` 当前也会按最小规则写入长期记忆
- 当前 memory summary 约定为：
  - `Governance warning: <reason>`
  - `Governance block: <reason>`
  - `Rule risk: <reason>`
  - `Rule block: <reason>`
- 这让 `recent_rule_feedback` 不再只是瞬时 prompt 信息

### 3.5 Relationship 侧

- 定义 relationship update policy 的最小接口
- 支持根据事件类型、地点类型、时段和角色语义调制增量
- 在 context builder 中派生 `relationship_level`
- 避免运行时更新无条件覆盖 seed 的 `relation_type`

## 4. 当前不建议立即做的内容

- 完整经济系统
- 商品与许可体系
- 完整组织治理建模
- 复杂 DSL
- 让 agent 直接读完整规则文件
- 群体心智（先做单 Agent，再考虑群体层面）
- 复杂情感计算模型（第一阶段简化即可）

先把 world 设计的基础资产层、解释链和心智模型打稳。

## 5. 下一步的具体实施建议

按当前代码状态，下一步应优先做：

### 5.1 治理增强（延续阶段4-5）

1. 选择性执法与观测概率模型，先采用无执法 agent 的平台级执行器
2. `policy` 到 relationship 后果层的映射继续细化，扩展到更多风险标签与地点语义
3. 更复杂的恢复机制与多因子衰减
4. reputation / director / relationship 三者的联动
5. agent-facing summary 与 memory/timeline 的统一 feedback schema

### 5.2 心智模型（阶段6，建议并行启动）

6. **Phase 6.1 情感层**：从 EmotionalState 类定义开始
7. **Phase 6.2 需求层**：定义 NeedState 类，与马斯洛层次映射
8. 情感层与需求层完成后，接入 Agent Context 和 World Rules Summary

### 5.3 认知模拟（阶段6后续，可选）

9. 社会议题态度建模（用于观点极化等实验）
10. 信息接触 → 认知更新规则
