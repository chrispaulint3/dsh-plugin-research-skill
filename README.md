# dsh-plugin-research-skill

用于 DSH/Cordis 插件本地开发、Skill 路由、任务分流与上下文隔离实验的独立 Skill 项目。

## 一句话安装（仅项目级）

在 **DSH 当前使用的 Git 项目根目录** 执行；不要传 `-g`：

```bash
cd /path/to/dsh-adaptive-execution
npx skills add chrispaulint3/dsh-plugin-research-skill --skill dsh-plugin-research -a universal -y
test -f .agents/skills/dsh-plugin-research/SKILL.md && echo "Project skill exists"
```

这会将 Skill 安装到当前项目 `.agents/skills/dsh-plugin-research/`，不污染全局目录。DSH `dsh-skill-filesystem` 默认发现 `<projectRoot>/.agents/skills/<name>/SKILL.md`。这里的 `projectRoot` 是 Agent 运行目录往上最近的 `.git` 目录；**不能仅从另一个项目启动 DSH，然后假设它会自动读取此项目的 Skill**。如果 DSH 的 Session 工作目录与安装目录不同，需要让 Agent 使用正确的工作项目，或者在隔离 Profile 中为文件系统 Provider 配置 `customSkillDirs` 指向该项目的 `.agents/skills` 绝对路径。

```bash
# 在安装项目内检查
pwd
git rev-parse --show-toplevel
npx skills list
ls -la .agents/skills/dsh-plugin-research
```

若 DSH 在容器/沙箱/远程主机运行，路径还必须对 DSH 文件系统可见。请在**新 Session** 检查 Skill Catalog；还要确保启用 Registry、Filesystem Provider 和 Consumer。

给 Coding Agent 的指令：

> 使用 dsh-plugin-research 检查我的 DSH 开发环境，确认版本与 Profile，验证 Tool Shadowing，然后开发、测试并对比算法效果；不要改动日常使用的 Profile。

## v1.1：适配 DSH Adaptive Execution v3.0

新增运行时观测、Tool 路由、反馈归因、经验学习规范及两个研究脚本。

```bash
S=.agents/skills/dsh-plugin-research
python3 "$S/scripts/policy_guard.py" --config "$S/fixtures/adaptive/recommend-config.json"
python3 "$S/scripts/experience_lab.py" audit --events "$S/fixtures/adaptive/events.jsonl"
python3 "$S/scripts/experience_lab.py" evaluate --events "$S/fixtures/adaptive/events.jsonl" --queries "$S/fixtures/adaptive/queries.jsonl" --k 1 --db .local/adaptive-eval.sqlite3
```

离线合成 Fixture 并不代表 DSH 实际调用；B0 原生运行必须单独观测。依旧只支持项目级安装，不加 -g。

## 能力

- Environment Doctor：只读检查 DSH、Node、pnpm、项目与 Profile
- Development Loop：最小修改、类型检查、单元和运行态验证
- Tool Shadowing：验证 Agent 作用域遮蔽，确保不误当作权限控制
- Experiment Loop：JSONL 标注与预测、SQLite 指标、Baseline/Candidate 对比
- Failure Analysis：失败样本、根因定位、回归实验

## 安装后的命令

```bash
S=.agents/skills/dsh-plugin-research
python3 "$S/scripts/doctor.py" --project . --profile adaptive-dev
python3 "$S/scripts/lab.py" self-test
python3 "$S/scripts/scaffold.py" --project .   # 只预览，不修改
```

项目本身也可直接运行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/lab.py self-test
```

所有评测 fixture 都是合成数据。离线 JSONL 指标不等于真实 DSH 端到端执行结果。修改 Cordis Hook、Tool Shadowing、Subagent 等能力后仍需在隔离 Profile 中验证。

## 项目结构

- `SKILL.md`：工作流与边界
- `references/`：按需读取的规范与研究资料
- `scripts/`：Python 标准库工具
- `fixtures/`：合成测试数据
- `tests/`：单元测试
- `.github/workflows/`：CI

这是 Skill 仓库，不是 DSH 插件。DSH 需启用 `@deepseek-ai/dsh-skill`、`@deepseek-ai/dsh-skill-filesystem`，以及负责向模型暴露 Skill 的 `@deepseek-ai/dsh-tool-skill`（或你自己的 Consumer）。建议在新 Session 中验证。正式以 GitHub 作为唯一分发源，不以 ZIP 发布。

当前版本首先通过 GitHub 源码提交发布；在实际 DSH 环境中仍需验证 Tool Shadowing 与真实 Agent E2E。

参考：[skills CLI](https://github.com/vercel-labs/skills) · [DSH](https://github.com/deepseek-ai/deepseek-harness)
