# Agent 算法实验协议

本 Skill 的 `lab.py` 是**离线评分器**，不会执行 DSH、不会生成预测；输入是人工标注的 labels JSONL 与算法预测 JSONL。

## Skill Retrieval
每行 labels 格式 `{"id":"s1","relevant_skills":["read-bug"],"forbidden_skills":["fix-bug"]}`。
每行 predictions 格式 `{"id":"s1","ranked_skills":["read-bug","fix-bug"]}`。
统计 Recall@K、Precision@K、Hit@K、MRR@K、Forbidden@K。空相关集必须明示。

## Task Routing
labels:`{"id":"t1","expected_mode":"direct"}`，predictions:`{"id":"t1","predicted_mode":"direct"}`。
允许模式：direct、fast、interactive、background。输出整体准确率与各类召回率。

## Context Projection
labels:`{"id":"c1","required_refs":["r1","r2"]}`，predictions:`{"id":"c1","retained_refs":["r1"]}`。
统计 Reference Recall 及多余引用比例；最终还要通过真实任务约束保留率验证。

## 基线约束
比较需要固定数据集 SHA256、K、模型、提示词和插件版本。离线报告写入 SQLite，不能证明真实 Agent 成功率变化。真实端到端评测应补任务完成率、上下文 Token、首次回答时延、工具错误及安全拒绝率。

## 示例
```bash
python3 scripts/lab.py self-test
python3 scripts/lab.py eval skill --labels fixtures/skills.labels.jsonl --predictions fixtures/skills.predictions.baseline.jsonl --db .local/experiments.sqlite3 --tag baseline
python3 scripts/lab.py history --db .local/experiments.sqlite3
```
比较两个 run ID 用 `python3 scripts/lab.py compare BASELINE_ID CANDIDATE_ID --db .local/experiments.sqlite3`。
