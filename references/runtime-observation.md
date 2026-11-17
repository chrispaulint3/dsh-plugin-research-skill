# Runtime Observation

P0 固定 DSH 版本并核对本地 tools/result、session/event、Feedback 事件的实际签名。Skill 只提供验证流程，不把 JSONL 离线审核器当作 DSH 原生事件监听器。

`off` 不采集，`observe` 仅旁路采集，`recommend` 只记录影子推荐，只有 `enforce` 可以更改 Agent 模型可见的 Tool/Skill。

采集需用稳定 session/call ID 去重；无法关联的事件记 unknown，不按时间邻近猜测因果。Skill 被加载不等于执行成功，Tool 返回 ok 不等于任务完成。默认不落原始提示词、工具参数和 Token。真实 DSH P0 Contract Test 必须基于本机 SDK 验证。
