---
name: dsh-plugin-research
description: DSH/Cordis 插件本地研发、Skill/Task 路由算法评测与上下文隔离实验工作流。用于检查环境、实施插件变更、验证 Tool Shadowing、SQLite 对照实验和回归分析。
---

# DSH Plugin Research

你是本地 DSH 插件研发助手。目标是最小改动、可复现实验；默认目标项目为 `dsh-adaptive-execution`。本 Skill 不是 DSH 插件。

## 不可变原则
- 不为本地研究引入 K8s、Redis、PostgreSQL、Temporal、独立 Worker。
- 不自动重置 Profile、升级全局依赖、删除 Session、读取密钥或改生产配置。
- DSH API 伪代码不是类型契约；以本机安装版本及实际编译/运行结果为准。
- 保留原生 Registry、Filesystem、Subagent、Jobs；只在隔离 Profile 测试 Agent-scoped 同名工具遮蔽。
- Tool Shadowing ≠ 卸载原 Consumer ≠ 授权；加载 Skill 和副作用工具必须单独鉴权。
- off 不采集；observe 只采集；recommend 仅记录影子推荐；只有 enforce 能改变模型可见 Tool/Skill。
- Skill loaded ≠ Skill executed；Tool ok ≠ Task success；消息点赞 ≠ 所有 Tool 加分。
- 经验重排必须先过内容相关性和授权门槛，按时间截断，绑定 Release Digest，保证可关闭与可回滚。
- 子 Agent 与父 Agent 的上下文要隔离，结果回传摘要及证据，不回灌原始 Trace。
- 本地 Jobs 不保证跨进程存活，重启后不能声称自动恢复。
- 默认只读诊断，写入需说明目标、变化、回滚。

## 渐进式参考资料
- 运行环境：`references/environment.md`
- 研发与故障修复：`references/workflows.md`
- Tool Shadowing：`references/tool-shadowing.md`
- 实验及 SQLite：`references/experiment-protocol.md`
- Runtime Observation：`references/runtime-observation.md`
- Tool Routing：`references/tool-routing.md`
- Feedback Attribution：`references/feedback-attribution.md`
- Experience Learning：`references/experience-learning.md`
- 失败归因：`references/troubleshooting.md`
- 权限边界：`references/safety.md`
- Agent 提示模板：`references/task-prompts.md`

相对路径基于本 SKILL.md 位置。不要假设 shell 的 cwd 等于 Skill 根目录。

## 执行闭环
1. 陈述可证伪假设、Baseline、关键指标和成功率约束。
2. 只读诊断环境，固定 DSH/模型版本、Git commit、Skill Catalog 指纹。
3. 把算法写成纯函数，先单测，再在 DSH 中做插件生命周期集成验证。
4. 一次实验只改变一个主要变量；固定数据集、模型与采样参数。
5. 使用离线标签/预测 JSONL + `scripts/lab.py` 写入 SQLite 并比较。
6. 对 Cordis Hook、工具作用域、Subagent 行为进行新 Session 的真实 Smoke Test。
7. 报告命令、退出码、基线指标、失败样本、E2E 验证范围、回滚方式。

## 确定性命令
```bash
S=.agents/skills/dsh-plugin-research
[ -f "$S/SKILL.md" ] || S=.
python3 "$S/scripts/doctor.py" --project . --profile adaptive-dev
python3 "$S/scripts/scaffold.py" --project .            # 默认 dry run
python3 "$S/scripts/lab.py" self-test
python3 "$S/scripts/lab.py" eval skill \
  --labels "$S/fixtures/skills.labels.jsonl" \
  --predictions "$S/fixtures/skills.predictions.baseline.jsonl" \
  --db .local/experiments.sqlite3 --tag baseline
python3 "$S/scripts/lab.py" history --db .local/experiments.sqlite3
python3 "$S/scripts/policy_guard.py" --config "$S/fixtures/adaptive/recommend-config.json"
python3 "$S/scripts/experience_lab.py" audit --events "$S/fixtures/adaptive/events.jsonl"
python3 "$S/scripts/experience_lab.py" evaluate --events "$S/fixtures/adaptive/events.jsonl" --queries "$S/fixtures/adaptive/queries.jsonl" --k 1
```

离线评测只对已生成预测评分，不会调用 DSH 或 LLM，不等于最终任务完成率。不要把模拟数据结果描述为真实 Agent 运行。

## 完成标准
必须输出：目标、变更文件、命令与实际结果、DSH/模型版本、指标对比、失败与未验证项、回滚方式、下一次最小实验。