# FAQ

适合读者：owner、新成员、训练与数据工程师  
依赖文档：[文档索引](index.md)、[术语表](glossary.md)  
相关入口：[入口目录](entrypoints.md)  
相关 contract：[Contract Catalog](contracts/README.md)  
最后更新意图：回答当前项目中反复出现的真实问题

## Tool-KG 是否参与训练 rollout？

不直接参与。KG 产生 grounded task；任务经执行和 postprocess 形成固定训练数据。
Formal training 不在 rollout 时查询 Tool-KG 或执行工具。

## Formal training 会不会调用 MCP？

不会。SFT、ToolRL、GAD、OPD 都遵守 offline training policy；生成 action 不执行。

## 为什么保留 `debug_one_task.py`？

模型训练后仍需要真实工具推理测试。它是显式 online debug，需 opt-in，不是训练入口。

## SFT、ToolRL、GAD 数据有什么区别？

SFT 消费完整 messages；ToolRL 把含工具调用的 assistant turn 切成 fixed state/reference
action；GAD 还保留 final-answer decision，并加入 current-student negatives/discriminator。

## 为什么不能从 repo 根直接运行某些 Slime 脚本？

DrugAgent training scripts假设从 `slime/` 运行，并依赖 `drug_agent.*`、Slime package、
worker environment 和运行时 `PYTHONPATH` 语义。不要引入 monorepo 包前缀替代它。

## 为什么 4B SFT smoke 默认 TP=4？

当前 wrapper 的注释和配置表明 TP=4 用于分摊大 vocabulary logits 及临时 clone，
并允许 DP=1、RBS=GBS=1 的保守 smoke。它是当前已验证配置，不是所有硬件的通用最优值。

## 为什么 `make check` 不跑训练？

它用于可重复的非侵入式仓库检查；训练、Ray、GPU、MCP 和模型加载依赖外部 worker 状态，
也会产生高成本副作用。

## Contract 都是完整 JSON Schema 吗？

不是。Catalog 明确区分 `model`、`validator`、`doc-only`；只有真实存在的能力才能登记。

## 如何判断脚本是 active、smoke、debug 还是 legacy？

查 `docs/entrypoints.md`。文件名只提供提示，不能代替状态和副作用登记。

下一步应该读：[阅读地图](reading-map.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)
