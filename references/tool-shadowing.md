# Agent Scoped Tool Shadowing 验证协议

## 意图
通过实验插件在适当的 Agent 工具作用域注册同名 `skill` 工具，遮蔽继承的 `dsh-tool-skill` 工具；复用 `ctx.skills`、Filesystem 和其他原生能力。此方式不是安全边界。

## 必须先核对
1. 记录本机 DSH、Cordis 版本。
2. 查验本机的 Agent 创建事件、`agent.ctx.tools.register`、`ctx.skills.get` 的**实际类型签名**。
3. 查验注册是否发生在 Agent scope，而不是全局同级产生重复注册。
4. 核验原生 Consumer 是否根据当前可见工具决定是否提供 Catalog；不得假设所有发布版本完全相同。

## 安全的 POC
- 使用 `adaptive-dev` 独立 Profile，不修改日常 Profile。
- 新 Session 中检查生效工具 identity、可见 Catalog 的实际 Token。
- 验证 `find_skill` + 自定义 `skill(name)` 能加载 Registry 中合法 Skill。
- 验证未授权/不可用 Skill 被拒绝，原生显式调用不能绕过权限。
- 测试子 Agent、Preset 切换、重复创建/销毁时没有残留 Hook 或重复工具。
- 插件关闭后原生功能正常。
- 旧 Session 注入的目录可能留在历史中：比较必须用**新 Session**。

## 兜底
若作用域遮蔽与当前发布版本不兼容，单独的实验 Profile 可显式禁用原始 Consumer；不要修改 DSH 内核。禁止把未经本机编译验证的示例当成可运行代码。

## 验收证据
实际运行命令、插件 commit、DSH 版本、工具解析结果、上下文 Token 变化、成功/拒绝的 Skill 调用案例。
