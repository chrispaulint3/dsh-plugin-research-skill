# 故障排查和回归

## DSH 仍然加载全部 Catalog
确认新 Session、实验 Profile、工具可见作用域、工具 identity、原生 Consumer 事件和构建产物是否是最新版本；检查子 Agent 是否复用了未遮蔽作用域。

## Plugin 加载失败
核对 DSH/Node 版本、package exports、Cordis 依赖注入、构建格式、插件清理函数。失败后优先恢复稳定 Profile。

## 编译成功但行为未改变
对比 `dsh --dump-config`（仅在本机当前版本支持时）、检查包链接与实际加载路径。重新构建并重启实验 Runtime，创建新 Session。

## JSONL 评测异常
确认每条记录有唯一非空 id、标签与预测 ID 集完全一致、列表无重复项、K 相同。不能偷偷丢弃失败样本或修补标签以优化分数。

## 失败分析格式
症状；预期；实际；最小复现；日志（脱敏）；归因（算法/Adapter/Runtime/权限/数据）；修复；回归结果；未验证的风险。
