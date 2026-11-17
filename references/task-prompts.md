# Coding Agent 请求模板

## 环境诊断
“使用 dsh-plugin-research，只读检查本地 DSH Profile、版本、插件源码位置与 SQLite 工具；列出不兼容点，不重置环境。”

## 研发任务
“使用 dsh-plugin-research，为 Skill Retriever 增加 BM25 基线。算法部分只写纯函数，先补测试，禁止引入向量数据库，运行单测后报告结果。”

## Runtime POC
“使用 dsh-plugin-research，在 adaptive-dev 环境验证 Agent-scoped Tool Shadowing。先检查本机类型签名，然后做新 Session Smoke Test，不修改 web 日常 Profile。”

## 离线评测
“使用 dsh-plugin-research，基于同一 labels JSONL 比较 baseline 和 candidate 的 Recall@3、MRR、Forbidden@3，记录 SQLite；明确标注离线结果与 DSH E2E 未验证。”

## 失败分析
“找出 Candidate 相比 Baseline 最严重的五个回归样本，归因、修复并追加回归测试；一次只改一个主要变量。”
