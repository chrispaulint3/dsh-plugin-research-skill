# dsh-plugin-research-skill

用于 DSH/Cordis 插件本地开发、Skill 路由、任务分流与上下文隔离实验的独立 Skill 项目。

## 一句话安装

在目标项目根目录执行：

```bash
npx skills add chrispaulint3/dsh-plugin-research-skill --skill dsh-plugin-research -a universal -y
```

给 Coding Agent 的指令：

> 使用 dsh-plugin-research 检查我的 DSH 开发环境，确认版本与 Profile，验证 Tool Shadowing，然后开发、测试并对比算法效果；不要改动日常使用的 Profile。

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

这是 Skill 仓库，不是 DSH 插件。需要从安装目标项目运行，并启用 DSH 文件系统 Skill Provider。正式以 GitHub 作为唯一分发源，不以 ZIP 发布。

参考：[skills CLI](https://github.com/vercel-labs/skills) · [DSH](https://github.com/deepseek-ai/deepseek-harness)
