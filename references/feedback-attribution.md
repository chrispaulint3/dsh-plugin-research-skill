# Feedback Attribution
不能把工具返回 ok、Skill 文档加载或用户点赞当成任务成功。拆分 technical_success、task_success、user_satisfaction、routing_quality。
不同来源的同一 call_key 只统计一次，缺失 call_key 不能按时间接近猜测因果。反馈 message-put 和 message-delete 用稳定 session/message/revision 幂等同步，删除后当前评分为空。
经验学习只接受 verified 且 direct attribution 的已验收 task/evaluated 记录，每 Task+Capability+Release 去重。实际 DSH Adapter 必须依据本机 SDK 确定事件字段。离线运行 scripts/experience_lab.py audit 查看合成数据的去重与反馈撤销。
