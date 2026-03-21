# Relationship Model

- 类型：`engineering`
- 状态：`draft`
- 负责人：`repo`
- 基线日期：`2026-03-21`

## 1. 目标

关系网络不应只是前端展示的一组数值条。

它应承担三类职责：

- 作为 agent 的长期社会状态
- 作为规则、治理和记忆系统的输入
- 作为 timeline 与 agent detail 的可解释输出

一句话：

**relationship 是世界中的长期社会状态，不是一次对话后的临时分数。**

## 2. 当前实现摘要

当前仓库已经有最小可用关系模型。

### 2.1 数据结构

当前关系以 run 级、有向记录持久化：

- `agent_id`
- `other_agent_id`
- `familiarity`
- `trust`
- `affinity`
- `relation_type`

特点：

- 是有向边，不是无向边
- 同一对角色允许 `A -> B` 与 `B -> A` 不同
- `familiarity` 范围为 `0..1`
- `trust` / `affinity` 范围为 `-1..1`

### 2.2 初始关系

当前支持从 agent 目录下的 `relations.yml` 读取初始关系，并在 seed 时写入数据库。

这意味着：

- bundle 或 agent 资产可以定义“开局关系”
- 如果没有 seed 数据，关系可从空白开始

### 2.3 运行时更新

当前运行时仍主要围绕社交事件更新关系，但已经不再是“无条件加分”的最初版本。

当前自动关系更新路径为：

- 当发生 `talk` / `speech` 事件时
- 对参与双方分别执行一次增量更新

当前默认基础增量仍是：

- `familiarity +0.1`
- `trust +0.05`
- `affinity +0.05`

但这个基础增量已经会被上下文继续调制：

- `policy.social_boost_locations` 可小幅提升 `affinity`
- `policy.sensitive_locations` 会削弱 `trust / affinity`
- `policy.talk_risk_after_hour` 会在晚时段削弱 `trust / affinity`
- `rule_evaluation.decision == soft_risk` 会进一步削弱关系增益
- `governance_execution.warn / block` 会进一步削弱关系增益
- actor 或 target 的 `governance_attention_score` 升高时，也会继续压低关系增益

当前每次关系更新还会把解释结果写回 event payload 的 `relationship_impact`，包括：

- `familiarity_delta / trust_delta / affinity_delta`
- `modifiers`
- `summary`
- `rule_decision / rule_reason / governance_decision / governance_reason`

### 2.4 当前局限

当前实现仍是最小版本，主要局限包括：

- 仍然没有真正的负向 delta，当前只是把正向增益削弱到接近 0
- 没有时间衰减
- 基础增量与阈值仍主要是硬编码常量，没有完全 policy 化
- 当前只覆盖 `talk / speech`，还没有扩展到冲突、帮助、失信等事件
- perception 虽然已经派生 `relationship_level`，但更细的暴露边界仍比较粗
- `relation_type` 仍更像 seed 标签，不是完整稳定语义层

## 3. 与 world design 的关系

relationship 不单独构成一套世界制度。

它在 world design 中更接近：

- `后果层` 的长期状态
- `agent visible summary` 的社会背景输入
- `rules` / `policy` 可引用的社会事实来源

因此应坚持以下边界：

- `rules.yml` 不直接保存关系状态
- `policies/*.yml` 不直接保存某两人的关系值
- relationship 变化由代码执行，但其变化条件应受规则与政策影响

一句话：

**关系是状态层，规则和政策是约束层。**

## 4. 设计原则

### 4.1 有向而非无向

默认继续采用有向关系。

原因：

- 社会关系天然可能不对称
- “我信任你” 与 “你信任我” 不必相等
- 更适合表达主体视角、cast 视角和误判

### 4.2 多维而非单值

默认不退回到单一“亲密度”。

第一版推荐保留三条核心轴：

- `familiarity`：认识和接触程度
- `trust`：可靠性与安全感判断
- `affinity`：情感亲近或好恶倾向

这三者含义应区分：

- 高频接触可以提升 `familiarity`
- 被帮助或被欺骗主要影响 `trust`
- 聊得来、相处舒适主要影响 `affinity`

### 4.3 关系类型是派生语义，不是唯一事实

`relation_type` 不应成为唯一真实来源。

更合理的定位是：

- 一部分来自初始资产，如 `family`、`colleague`
- 一部分可由系统派生为展示或 prompt 语义，如 `friend`、`close_friend`

这意味着：

- `relation_type` 可以是“社会标签”
- 底层判断仍应优先依赖数值状态和显式规则

### 4.4 增减必须可解释

关系变化不应只是“发生对话就加分”。

更合理的做法是：

- 由事件类型决定变化方向
- 由场景、地点、时段、角色关系决定变化幅度
- 在需要时把变化原因写入 event payload 或 memory

## 5. 推荐的关系演化模型

### 5.1 正向变化

推荐第一阶段支持的正向来源：

- 日常对话
- 持续陪伴
- 协助、安慰、保护
- 在社交增强地点的自然互动
- 多日持续的稳定接触

默认影响建议：

- 普通对话：小幅提升 `familiarity`
- 愉快互动：中小幅提升 `affinity`
- 帮助或可靠兑现：中幅提升 `trust`

### 5.2 负向变化

推荐第一阶段支持的负向来源：

- 冲突、争吵、拒绝
- 欺骗、失约、背叛
- 在敏感场景中的异常施压或操控
- 长期冷漠或明显疏远

默认影响建议：

- 冲突先伤 `affinity`
- 失信先伤 `trust`
- 长期疏离可缓慢降低 `affinity`

当前实际代码状态：

- 已实现“风险或治理削弱关系增益”
- 尚未实现“关系值出现明确负向扣减”
- 因此目前更准确地说是 `growth suppression`，而不是完整的负向演化模型

### 5.3 时间衰减

关系不应永久只涨不跌。

建议引入轻量衰减：

- `familiarity` 衰减最慢，甚至可仅在极长期无接触时下降
- `affinity` 在长期无互动时缓慢回落
- `trust` 不因短期无互动大幅下降，但可在长期缺乏验证时回归中性

### 5.4 上下文调制

关系更新幅度应允许被上下文调制。

优先引入的调制项：

- `world.time_period`
- `target_location.type`
- `policy.social_boost_locations`
- `policy.sensitive_locations`
- `policy.subject_protection_bias`
- actor / target 的 `world_role`

例如：

- 在 `cafe`、`plaza` 中的自然社交可获得更高 `affinity` 增益
- 在深夜或敏感区域的异常接触不一定增进关系，甚至可能带来负反馈

当前已落地的最小调制项：

- `policy.social_boost_locations`
- `policy.sensitive_locations`
- `policy.talk_risk_after_hour`
- `rule_evaluation.decision / risk_level / reason`
- `governance_execution.decision / reason`
- actor / target 的 `governance_attention_score`

## 6. 与规则和政策的边界

relationship 更新不应直接硬编码在持久化层里完成全部语义判断。

推荐链路：

1. 动作与事件先进入规则裁决层
2. 规则层判断其是否 `allowed` / `violates_rule` / `soft_risk`
3. 治理执行层决定是否观察到、是否介入、是否产生日志或处罚
4. 后果层再更新 relationship / memory / alert score

这样可以表达：

- 社交发生了，但属于高风险
- 社交被拦截了，因此不更新或反向更新关系
- 社交虽发生，但因敏感环境导致信任下降

## 7. 与 agent 可见摘要的关系

relationship 原始数值不一定直接暴露给 agent。

更适合暴露的是派生后的社会语义，例如：

- `stranger`
- `acquaintance`
- `friend`
- `close_friend`
- `family`

以及有限的可见信息，例如：

- 只对熟人暴露职业
- 只对密友暴露更深背景
- 对陌生人仅暴露可观察线索

这层应由 runtime context 负责组装，而不是让 agent 直接读取数据库关系行。

## 8. 第一阶段推荐落地范围

为了和当前仓库复杂度匹配，relationship 第一阶段建议只做：

- 保留当前三维数值模型
- 明确保留有向边
- 支持 seed 初始关系
- 支持事件驱动更新
- 支持基于 `policy` 的增益或惩罚调制
- 在 perception 中派生 `relationship_level`

当前已完成：

- 保留三维数值模型
- 保留有向边
- 支持 seed 初始关系
- 已支持最小 `policy / rule / governance / attention` 调制
- 已在 runtime context 中派生 `relationship_level`
- 已把关系变化解释写回 `relationship_impact`

当前仍未完成：

- 真正的负向事件驱动扣减
- 时间衰减
- 增量参数的完整 policy 化
- 更复杂的双边非对称后果模型

第一阶段不建议做：

- 完整社会图算法
- 群体声誉传播
- 复杂八维人格化关系模型
- 组织层级、家族法谱系等重资产系统

## 9. 对当前仓库的直接修正建议

按优先级，当前最值得先修的点是：

1. 从“只覆盖 `talk/speech`”扩展到更多事件类型，如帮助、冲突、失信
2. 引入至少一类真正的负向关系扣减，而不只是削弱正向增长
3. 引入最小时间衰减
4. 把当前硬编码增量与阈值继续搬进 `policy`
5. 继续扩展 `relationship_impact` 与 memory / director 的联动
6. 避免后续运行时演化无条件覆盖已有 `relation_type`

## 10. 默认结论

relationship 在当前项目中应被定义为：

- run 级长期社会状态
- 由事件驱动、可双向不对称演化的有向图
- 受 `rules` / `policy` / enforcement 影响的后果层数据
- 向 agent 暴露派生语义，而不是原始数据库实现细节

这一定义既兼容当前最小实现，也为后续 world design 落地保留了清晰边界。
