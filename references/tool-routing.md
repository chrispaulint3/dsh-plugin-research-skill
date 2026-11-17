# Tool Routing 研究协议
Skill 与 Tool 维护不同能力键及 Release。候选必须来自当前 Agent scope 真实可见的 Tool Schema，检索前做授权过滤和相关性判定，允许 none-of-the-above。
recommend 仅记影子推荐，不更改任何模型可见工具；enforce 只能在实验 Profile 中修改可见性，执行时仍要鉴权。技术调用 ok 不能代表任务成功，Schema 变更后旧经验失效。
基准要包含：相近工具歧义、无权限但相关、常用但不相关、多 Tool 组合、拒选与版本变化。
