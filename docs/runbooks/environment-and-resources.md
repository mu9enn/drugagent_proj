# Environment And Resources

适合读者：准备 GPU worker、checkpoint、Ray/SGLang 资源的训练与排障人员  
依赖文档：[训练 runbook](training-sft-toolrl-gad.md)、[已知问题](../known-issues.md)  
相关入口：环境检查、torch_dist 准备、所有 `ray-gpu` 入口  
相关 contract：无；本页描述运行时假设  
最后更新意图：记录当前 worker 假设与资源风险，不改变路径或默认值

## 当前路径与服务假设

- training wrappers source worker-local Slime environment script，并 `cd "$SLIME"`。
- `$VERL_DATA` 保存模型、torch_dist 数据、转换数据和运行产物。
- Ray worker runtime `PYTHONPATH` 包含 `/root/Megatron-LM/`、`$SLIME` 和 worker 修复目录。
- Qwen3.5-4B 训练需要对应 HF checkpoint 与 torch_dist checkpoint。
- Ray 负责 job submission；colocated SGLang 负责 rollout/model generation。

这些路径有意保持现状，仓库静态检查不保证它们在目标 worker 存在。

## GPU 与内存

- 当前 4B SFT smoke wrapper 面向四张 H200，默认 TP=4；代码注释说明这是为分摊大
  vocabulary logits 及其临时 clone，并允许最小 RBS=GBS=1。
- colocated SGLang 的 `TorchMemorySaver` 与 inherited
  `expandable_segments` allocator setting 不兼容；formal wrappers 会移除该设置。
- 单条长 ReAct 样本仍可能 OOM，dynamic batching 不会自动截断超长单样本。
- Ray/SGLang/Megatron 可能同时占用大量 host RAM。

**待 owner 确认的运维经验**：128 GB host RAM 被报告为高风险；192 GB/256 GB 是建议容量。
当前代码没有编码这些阈值，不能把它们当作自动检查或硬性保证。

## 检查安全等级

| 检查 | 静态安全 | 可能触发 GPU/模型/远程 |
| --- | --- | --- |
| `ls`、`git grep`、阅读脚本、`bash -n`、`py_compile` | 是 | 否 |
| `make check` / contract / active tests | 设计上是 | 否 |
| `check_env.sh` | 以入口目录标注为准；当前 read-only | 不应 |
| torch_dist preparation | 否 | 模型加载/GPU、local-write |
| 任意 training wrapper | 否 | Ray/GPU/SGLang/model |
| online MCP debug | 否 | remote MCP，部分还会 GPU/SGLang |

下一步应该读：[Troubleshooting](troubleshooting.md)  
如果要修改相关代码，请先读：[开发者指南](../developer-guide.md)
