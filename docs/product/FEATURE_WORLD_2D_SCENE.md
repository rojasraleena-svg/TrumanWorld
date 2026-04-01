# Truman World 前端 Godot 2D 场景接入方案

- 类型：`feature`
- 状态：`proposal`
- 负责人：`frontend`
- 最后更新：`2026-03-11`
- 适用范围：`frontend/ world page / Railway deployment`

## 1. 文档目的

本文档用于回答一个具体问题：

> 当前 Truman World 项目，是否值得把世界页从 SVG/DOM 地图升级为基于 Godot Web 的 2D 场景，以及应当如何接入。

目标不是设计一个完整游戏客户端，而是为当前导演控制台补一层更强的世界渲染能力。

## 2. 当前现状

当前前端世界页已经不是空白页，而是一个可运行的实时世界视图：

- [`frontend/app/runs/[runId]/world/page.tsx`](../../frontend/app/runs/[runId]/world/page.tsx) 负责世界页容器
- [`frontend/components/world-canvas.tsx`](../../frontend/components/world-canvas.tsx) 负责世界视图编排
- [`frontend/components/town-map.tsx`](../../frontend/components/town-map.tsx) 负责 SVG 地图、地点、动线、缩放和昼夜表现
- [`frontend/components/world-context.tsx`](../../frontend/components/world-context.tsx) 负责世界快照轮询
- [`frontend/lib/types.ts`](../../frontend/lib/types.ts) 已定义世界快照、地点、事件、世界时钟等前端数据结构

结论：

- 现有项目已经具备世界数据流
- 现有项目已经具备世界页信息架构
- 真正需要替换的是地图渲染层，而不是整个前端

## 3. 架构结论

推荐方案：

- 保留 `Next.js` 作为前端壳层
- 保留 `React + SWR` 作为世界状态单一数据源
- 保留现有右侧面板、时间线、详情弹窗
- 仅将 [`frontend/components/town-map.tsx`](../../frontend/components/town-map.tsx) 的渲染职责替换为 `GodotWorldHost`

不推荐的方案：

- 不建议把整个前端页面改写为 Godot
- 不建议让 Godot 直接请求后端 API
- 不建议第一版就把全部控制 UI 搬进 Godot

一句话：

> Godot 应该是 Truman World 世界页的 2D 渲染子系统，而不是前端主框架。

## 4. 接入后能达到的效果

从产品表现看，世界页会从“抽象信息地图”升级为“可观看的小镇舞台”。

第一版预期效果：

- 小镇有固定 2D 场景背景
- 地点变成建筑或区域，而不是纯节点
- agent 变成可见角色 sprite
- 角色在地点之间移动时有平滑动画
- 昼夜变化体现在场景氛围上
- 热点地点可以被直接看见
- 对话以冒泡形式浮现在场景中

用户能直接观察：

- 谁现在在哪
- 谁刚从哪移动到哪
- 谁在和谁交谈
- 哪个地点正在成为剧情中心

## 5. 为什么值得做

### 5.1 产品表达收益

当前世界页更偏“仿真控制台”。

接入 Godot 后，Truman World 会更像一个：

- 可观看的 AI 小镇
- 可被导演观察的社会舞台
- 具有叙事感的实时仿真界面

这会显著提升：

- Demo 说服力
- 外部展示效果
- 产品辨识度
- 用户对世界运行的第一眼理解

### 5.2 可读性收益

很多本来需要打开详情才能理解的信息，会变成主画面可读：

- 地点是否拥挤
- 居民是否正在聚集
- Truman 是否被围绕、引导或孤立
- 某段剧情是否正在发生

### 5.3 导演系统解释性收益

项目已有 `director / planner / scene_goal` 相关能力。

Godot 场景配合对话冒泡后，用户会更容易看到导演干预的结果：

- 某个地点突然升温
- 某些角色被引导到同一场景
- 某段对话在关键时机出现
- 某次干预是否影响了 Truman 的体验

## 6. 为什么不能直接“全量游戏化”

虽然 Godot 能力很强，但 Truman World 当前的核心仍是：

- 仿真
- 解释
- 导演观察

而不是完整可玩游戏。

因此第一版应明确避免：

- 室内子场景
- 复杂寻路系统
- 大量可交互游戏 UI
- 重型战斗式状态机
- 与仿真无关的过度特效

原则：

> 先让世界可观看，再考虑让世界更华丽。

## 7. 推荐的页面结构

世界页整体结构不建议大改，继续沿用现有三栏布局：

- 顶部：标题 + 世界状态栏
- 左侧：Godot 世界场景
- 中间：世界健康度 + 地点详情
- 右侧：故事时间线
- 弹窗：Agent / Location / Timeline 详情

这样做的好处：

- 保持已有信息架构
- Godot 只承担世界渲染职责
- 不影响现有世界页的操作习惯

## 8. 推荐的模块边界

### 8.1 React 负责

- 获取世界快照
- 轮询和缓存
- 右侧面板和弹窗
- 时间线与系统控制
- 把世界数据整理成场景 DTO
- 处理 Godot 交互回传

### 8.2 Godot 负责

- 地图背景和建筑层
- agent 角色 sprite
- 移动动画
- 镜头缩放和拖拽
- 热点高亮
- 对话冒泡渲染
- 命中检测与点击回传

### 8.3 后端负责

- 世界状态权威数据
- 结构化事件
- 对话事件中的可展示文本
- 继续维持当前 API 语义

## 9. 数据桥接原则

不建议让 Godot 直接消费完整 `WorldSnapshot`。

推荐由 React 整理成更窄的 DTO，再发给 Godot。

推荐 DTO 类型：

- `SceneLocation`
- `SceneAgent`
- `SceneBubbleEvent`
- `SceneSelectionState`

推荐消息方向：

React -> Godot

- `scene_sync`
- `bubble_enqueue`
- `selection_sync`

Godot -> React

- `location_clicked`
- `agent_clicked`
- `bubble_clicked`

这样做的好处：

- 降低 Godot 对后端协议的耦合
- 允许 React 持续作为唯一业务编排层
- 未来替换渲染器时成本更低

## 10. 对话冒泡设计结论

对话冒泡应该做，而且优先级很高。

原因：

- 角色移动只能说明“人在移动”
- 对话冒泡才能说明“剧情在发生”

但冒泡不能做成聊天窗口，而应当是“事件可视化层”。

### 10.1 冒泡显示原则

- 只显示 `talk` 类事件
- 默认只显示短文本
- 普通事件短停留，重要事件长停留
- 同一地点同时最多显示 `1-2` 个冒泡
- 同一角色短时间内不要连续弹太多

### 10.2 冒泡文本来源

前端需要稳定可展示文本。

推荐在事件 payload 中补一个字段：

```json
{
  "display_text": "Truman 小声问 Bob 今天会不会下雨"
}
```

前端和 Godot 应优先依赖 `display_text`，而不是临时拼模板句。

### 10.3 冒泡定位

优先级从高到低：

- actor 头顶
- actor 与 target 中点
- location 锚点

### 10.4 冒泡与时间线联动

- 点击冒泡后，打开时间线并定位到对应事件
- 时间线选中事件后，Godot 场景高亮相关地点或角色

## 11. Railway 部署可行性

结论：可以继续使用 Railway 部署。

当前仓库已经具备 Railway 友好的结构：

- [`frontend/railway.toml`](../../frontend/railway.toml)
- [`backend/railway.toml`](../../backend/railway.toml)
- [`docs/operations/RAILWAY_DEPLOYMENT.md`](../operations/RAILWAY_DEPLOYMENT.md)

推荐继续保持：

- `frontend` 服务：Next.js，对外公开
- `backend` 服务：FastAPI，私网访问
- `postgres` 服务：数据库

Godot Web 导出产物建议直接挂在 `frontend/public/godot/world/` 下，由现有前端服务托管。

### 11.1 Railway 没有阻塞点

Godot Web 导出本质是静态文件：

- `.html`
- `.js`
- `.wasm`
- `.pck`

这类文件可以由现有 `frontend` 服务托管，不需要新建独立渲染服务。

### 11.2 真实需要关注的问题

真正的复杂点不在 Railway，而在 Godot Web 导出模式。

如果使用单线程 Web 导出：

- 最省事
- 更适合第一版

如果使用多线程 Web 导出：

- 需要额外响应头
- 涉及 `COOP / COEP`
- 部署和调试成本更高

因此第一版建议优先采用：

- `Godot 4.x`
- `GDScript`
- 单线程 Web 导出

## 12. 预估代码量

### 12.1 最小可用 PoC

- `600 - 1200` 行

包含：

- React 宿主组件
- React/Godot 通信桥
- Godot 初始化
- 地点和角色静态渲染
- 点击回传

### 12.2 可上线第一版

- `1500 - 3000` 行

包含：

- 上述 PoC 全部内容
- move 动画
- 镜头缩放和拖拽
- 热点高亮
- 对话冒泡
- 构建和部署接入

### 12.3 偏游戏化版本

- `3000 - 6000+` 行

包含：

- tilemap 和分层场景
- 更完整角色状态机
- 更复杂氛围特效
- 更强镜头与剧情演出

## 13. 推荐实施顺序

### Phase 1：渲染替换

- 新建 `GodotWorldHost`
- 输出场景 DTO
- Godot 渲染地点和角色
- 保持现有右侧面板不动

目标：

- 证明 Godot 可以稳定嵌入当前前端

### Phase 2：移动与交互

- 接入 move 事件动画
- 支持点击地点与角色
- 支持镜头拖拽与缩放

目标：

- 让世界真正“动起来”

### Phase 3：对话冒泡

- 接入 `talk` 事件
- 实现场景冒泡
- 联动时间线

目标：

- 让世界不仅可见，而且可理解

### Phase 4：氛围增强

- 昼夜增强
- 热点视觉强化
- 导演聚焦效果

目标：

- 提升场景叙事感，而不破坏可读性

## 14. 最终建议

建议做，但要控制边界。

最值得投入的部分是：

- 角色可见
- 移动可见
- 对话可见

最不值得第一版投入的部分是：

- 复杂游戏玩法
- 室内场景系统
- 过度视觉特效

最终目标不应是“把 Narrative World 做成游戏”，而应是：

> 把 Narrative World 做成一个用户愿意停下来观看、并能直接看懂社会互动正在发生的活世界。
