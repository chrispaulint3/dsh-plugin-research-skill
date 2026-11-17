# 最小研发工作流

## Development
1. 在目标插件仓库定位受影响模块；阅读现有测试。
2. 写出行为契约，明确哪些路径不应该改变。
3. 先写失败单测，只修改最少代码。
4. 运行 typecheck、测试；如改变 Hook、Scope 或 Tool，执行真实 DSH Smoke Test。
5. 记录修改、执行命令与退出码，说明未验证的运行态行为。

## 开发层次
L1：纯算法单元测试，避免 DSH 依赖。
L2：Adapter、SQLite、生命周期清理契约测试。
L3：真实 DSH 和新 Session 的集成验证，尤其 Tool Shadowing。
不得用 L1/L2 的通过替代 L3。

## 避免范围蔓延
- 不为了 Skill 检索开发新的 Agent Runtime。
- 不把 Skill 说明当作执行权限。
- 不让 DSH 的实验性 Catalog Consumer 破坏日常研发入口。
- 不在同一次实验修改算法、模型、Prompt、数据集等多个变量。

## 可交付
源码变更、最小复现、基线与候选评测、回滚步骤。


## v3.0 阶段映射
P0：核对真实 SDK API 与四种模式副作用；P1：observe 采集、事件去重、SQLite；P2：recommend 下的 Skill/Tool 影子候选；P3：verified/direct 的历史排序；P4：显式 Fast/Deep、独立 Subagent 与 Task Brief；P5：B0/B1/B2、时间切分、消融与真实 E2E。

Skill 本身不承担插件 Runtime 代码；修改算法、真实数据采集、权限和持久状态只能放在被测插件仓库。每次测试记录实际结果与回滚方式。
