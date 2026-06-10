# Reader-Oriented Map

适合读者：需要快速选择阅读顺序的 owner、新成员和工程师  
依赖文档：[文档索引](index.md)  
相关入口：[入口目录](entrypoints.md)  
相关 contract：[Contract Catalog](contracts/README.md)  
最后更新意图：按任务给出最短阅读路径，而不是重复实现细节

## 阅读路径

1. **Owner 检查主线**：`architecture.md` -> `mainline-flow-deep-dive.md` ->
   `known-issues.md` -> `entrypoints.md`。
2. **新成员理解项目**：`index.md` -> `glossary.md` -> `architecture.md` ->
   `data-lifecycle.md` -> `training-methodology.md`。
3. **生成数据**：`runbooks/data-generation-and-postprocess.md` ->
   `data-lifecycle.md` -> `contracts/contract-guide.md`。
4. **训练 SFT / ToolRL / GAD**：`training-methodology.md` ->
   `runbooks/training-sft-toolrl-gad.md` ->
   `../slime/drug_agent/OFFLINE_TRAINING_POLICY.md`。
5. **Debug MCP / online evaluation**：
   `runbooks/debug-and-online-evaluation.md` -> `entrypoints.md`。
6. **改 postprocess / contract / reward**：`developer-guide.md` ->
   `contracts/contract-guide.md` -> 对应 producer README 和测试。

## 运行前的副作用判断

| 标签 | 含义 | 运行前动作 |
| --- | --- | --- |
| `read-only` | 验证或检查；可能产生 Python cache | 可在开发机运行 |
| `local-write` | 写数据、报告、日志或 checkpoint | 先确认输出目录 |
| `remote` | 调用 Claude、MCP、provider 或下载 | 先确认凭据、配额和目标 |
| `ray-gpu` | 启动 Ray、SGLang、模型或 GPU 训练 | 只在正确 worker 上运行 |

组合标签表示同时具备多个副作用。`debug` 不等于安全，online debug 可能真实调用 MCP。

## 文档不保证的外部条件

- worker-local 模型、checkpoint、环境脚本和 `/root/Megatron-LM` 存在；
- `$VERL_DATA` 指向正确数据盘；
- MCP、Claude/provider、GAD discriminator 或本地 HTTP 服务可达；
- GPU 拓扑、host RAM、Ray 和 SGLang 满足运行需要；
- imported Slime 的所有上游示例都适用于 DrugAgent 主线。

下一步应该读：[主线架构](architecture.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)
