# Contract Guide

适合读者：contract producer/consumer、reviewer、测试维护者  
依赖文档：[Contract Catalog](README.md)、[数据生命周期](../data-lifecycle.md)  
相关入口：各 contract 的 producer/validator 路径见 `catalog.json`  
相关 contract：本页解释 `docs/contracts/catalog.json` 中的全部条目  
最后更新意图：定义兼容维护流程，不把 doc-only contract 冒充 schema

## Catalog 条目

| ID | Owner / Producer | Consumer | Level / Status | 当前验证与风险 |
| --- | --- | --- | --- | --- |
| `molclaw_kg_internal_models` | molclaw-kg | molclaw-kg | model / active | 显式代码模型；跨阶段语义仍需测试 |
| `trajectory_v2_graph` | KG Stage3 | KG adapter | validator / active | adapter builder 验证 |
| `kg_task_spec` | KG adapter | task execution | doc-only / active | 依赖文档和实现读取，风险较高 |
| `complete_session` | claude_agent | exporter/postprocess | doc-only / active | stream 兼容性由 consumer 容错承担 |
| `trajectory_exports` | trajectory exporter | scan | doc-only / active | 质量门字段变化可能静默影响 scan |
| `react_sft` | post_process_sft | SFT/ToolRL/GAD | validator / active | 有协议/schema 文档和 Slime validator |
| `rl_prompt` | post_process_sft | prompt consumers | doc-only / active | 无独立 validator |
| `toolrl_step` | ToolRL converter | offline ToolRL | validator / active | 有离线数据 validator |
| `gad_step` | GAD converter | GAD Stage2/3 | doc-only / active | 依赖 converter 和训练读取 |

`catalog.json` 是唯一索引；本表只解释，不取代它。当前 catalog 只使用 `active`，
没有条目被标为 `legacy-read-compatible`、`deprecated` 或 `removed`。

## 修改流程

1. 确认 producer owner、全部 consumer、当前 level 和 status。
2. 用 `git grep` 找字段、版本和 reader；不要只查一个子项目。
3. 新增字段默认 optional，保持旧 reader 可工作；语义变化考虑新版本。
4. 删除字段前先让 consumer 停止依赖，并明确迁移/恢复方式。
5. 更新 producer 定义、validator、golden sample 和 `catalog.json`。
6. 运行 `make test-contracts`、`make test-active`，再检查真实样本。

## Golden Sample 原则

- 选最小但代表关键结构的输入/输出。
- 比较关键字段、消息顺序、状态边界和 rejection reason。
- 不要求时间戳、绝对路径、临时目录等非确定字段 bitwise 相同。
- validator-level contract 应覆盖合法与非法样本；doc-only contract 至少覆盖 consumer
  能读取的代表样本，并明确这不等于完整 schema 验证。

## 兼容策略

- **新增字段**：优先 optional；consumer 忽略未知字段。
- **删除字段**：先废弃、迁移 consumer、保留读取兼容，再删除。
- **改变语义**：不要复用旧 version 名；记录 producer/consumer 切换点。
- **状态变更**：只有实现真实支持时才标 `legacy-read-compatible`；删除后记录在
  `docs/legacy-removals.md`。

下一步应该读：[数据生命周期](../data-lifecycle.md)  
如果要修改相关代码，请先读：[开发者指南](../developer-guide.md)
