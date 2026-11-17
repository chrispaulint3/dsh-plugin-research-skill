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
