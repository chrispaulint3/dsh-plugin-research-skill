# DSH 开发环境

## 首选架构
- 普通使用 DSH 保持稳定 Profile，实验用独立 `adaptive-dev`，自动评测用 `adaptive-eval`。
- DSH CLI 使用固定的已验证版本。本项目不 Fork DSH；只有调试核心时才拉官方源码。
- 插件与本 Skill 是两个独立仓库。插件属于产品，Skill 只规范 Coding Agent 的研发流程。

## 先检查，后操作
```bash
node -v
pnpm -v
python3 --version
dsh --version
dsh --help
git status --short
python3 scripts/doctor.py --project . --profile adaptive-dev
```
不要使用初始化 Profile 的命令重复覆盖已有配置；先确认 CLI 版本和帮助文本。不能推断特定 DSH 版本支持某个参数。

## 修改后的重启策略
- 纯函数算法/评测器：直接 Vitest 或 Python 单测，不重启 DSH。
- Cordis apply/hook、工具注册、Subagent 适配：编译后重启实验 Profile，使用新 Session 验证。
- HMR 不等于服务端插件热重载。没有明确验证时采用保守的进程重启。
- 插件构建文件和运行时加载路径必须一致；确认实际导入的是本次构建版本。

## 记录
DSH 与 Node 版本、系统架构、插件 commit、Profile、模型/温度、数据集哈希、实验 ID。脱敏后保存日志，严禁提交密钥。
