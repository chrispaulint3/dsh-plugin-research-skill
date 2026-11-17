# Experience Learning 研究协议
B0：真实原生 DSH 执行；B1：内容相关性排序；B2：B1 + 有证据的历史重排。历史只允许发生在查询 as_of 之前，按 intent + capability + release_digest 分组。
仅 verified/direct 的已验收任务贡献成功/失败。Beta(1,1) 平滑，少于 minEvidence=5 时不加权；maxHistoryWeight=0.15，且经验不能绕过授权和内容相关性门槛。Release 更新降为冷启动；消息点赞或技术调用成功不直接贡献 task_success。
离线执行：python3 scripts/experience_lab.py evaluate --events fixtures/adaptive/events.jsonl --queries fixtures/adaptive/queries.jsonl --k 1。
以上是合成用例的排名演示，不能推出真实 E2E 收益。实验应使用时间切分、能力版本锁定和消融研究。
