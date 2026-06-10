# Troubleshooting

适合读者：数据、训练、环境和 MCP 排障人员  
依赖文档：[环境与资源](environment-and-resources.md)、[入口目录](../entrypoints.md)  
相关入口：按每个问题所列入口；运行前确认副作用  
相关 contract：问题涉及数据时查 `docs/contracts/catalog.json`  
最后更新意图：保留可复用排障事实；证据不足处明确标注

## `No user query found in messages`

- **症状**：loss mask/消息解析报告找不到 user query。
- **典型日志片段**：`No user query found in messages`。
- **根因**：消息边界或模板不满足 mask 预期。
- **立即处理**：检查输入 messages 与 `qwen3_5` mask 调试结果。
- **长期修复**：用 validator/golden sample 保护消息边界；不要在排障时改 mask 行为。
- **相关文档/入口**：训练方法、`debug_sft_mask_qwen.py`。

## RBS 小于或不能整除 GBS

- **症状**：脚本在 Ray 前退出。
- **典型日志片段**：`ROLLOUT_BATCH_SIZE must be >= GLOBAL_BATCH_SIZE`。
- **根因**：SFT smoke batch 约束不满足。
- **立即处理**：选择满足 wrapper 明示约束的 RBS/GBS。
- **长期修复**：在提交训练前静态核对 batch/parallel 组合。
- **相关文档/入口**：训练 runbook、SFT wrapper。

## 4B TP=1 `logits.clone()` CUDA OOM

- **症状**：4B 路径在 logits 临时副本附近 OOM。
- **典型日志片段**：通常包含 CUDA OOM 与 logits/clone 调用栈。
- **根因**：当前项目注释记录 TP=1 无法分摊大 vocabulary logits 临时 clone。
- **立即处理**：使用已验证的 4B TP=4 smoke 配置。
- **长期修复**：任何新拓扑先独立做受控 smoke。
- **相关文档/入口**：环境与资源、4B SFT smoke wrapper。

## TorchMemorySaver 与 `expandable_segments`

- **症状**：colocated SGLang/TorchMemorySaver 启动或保存内存失败。
- **典型日志片段**：包含 `expandable_segments` / `TorchMemorySaver` incompatibility。
- **根因**：allocator setting 不兼容。
- **立即处理**：确认 formal wrapper 已移除 inherited setting。
- **长期修复**：不要从外部 runtime env 重新注入。
- **相关文档/入口**：所有 formal training wrappers。

## Ray Host Memory OOM

- **症状**：Ray worker 被 host memory pressure/OOM 杀死。
- **典型日志片段**：Ray memory monitor、worker killed 或系统 OOM。
- **根因**：Ray、SGLang、Megatron 和数据同时占用 host RAM；精确阈值依 workload。
- **立即处理**：停止并清理残留进程，降低并发/批量，检查目标 worker RAM。
- **长期修复**：记录真实峰值并据此定容量。128/192/256 GB 仅为待 owner 确认经验。
- **相关文档/入口**：环境与资源。

## `generation_config.json` Missing Warning

- **症状**：模型加载日志提示缺少 generation config。
- **典型日志片段**：包含 `generation_config.json` 和 missing/not found。
- **根因**：当前仓库证据不足；可能是 checkpoint 资产不完整或 loader 的可选 warning。
- **立即处理**：确认模型目录完整，并判断训练是否实际失败。
- **长期修复**：由 owner 用一次真实 worker 日志确认后再固化处置。
- **相关文档/入口**：环境与资源。状态：待确认。

## `No CUDA runtime found` Warning

- **症状**：导入或构建阶段提示未找到 CUDA runtime。
- **典型日志片段**：`No CUDA runtime is found`。
- **根因**：当前仓库未编码唯一根因；可能是开发机或 worker CUDA 环境。
- **立即处理**：开发机静态检查可忽略；GPU 任务则核对 driver/runtime/container。
- **长期修复**：区分静态开发环境与训练 worker。
- **相关文档/入口**：环境与资源。状态：证据不足，勿视作固定 blocker。

## MoE Dispatcher Warning

- **症状**：启动日志出现 MoE token dispatcher 配置 warning。
- **典型日志片段**：包含 `moe-token-dispatcher-type`。
- **根因**：模型/并行配置相关；当前 DrugAgent 证据不足以给出统一根因。
- **立即处理**：核对当前 model args 与对应 Slime/Megatron 支持。
- **长期修复**：为实际使用的 MoE 配置保留受控 smoke 记录。
- **相关文档/入口**：模型 args、Slime 文档。状态：待具体日志确认。

## MCP Connection Refused

- **症状**：online debug 或 raw session observation 出现 connection refused。
- **典型日志片段**：`connection refused`。
- **根因**：目标 MCP 未启动/不可达；postprocess validator 也会识别该错误。
- **立即处理**：仅在 online debug 中检查 endpoint、凭据和网络；失败样本查看 quarantine/rejection。
- **长期修复**：保持 formal training 无 MCP，在线入口做显式 health check。
- **相关文档/入口**：online debug runbook、postprocess reports。

## 旧 `git_cl.drugagent_proj` Import 污染

- **症状**：离开特定机器目录后 import 失败。
- **典型日志片段**：`ModuleNotFoundError: git_cl...`。
- **根因**：机器路径被写入 Python import。
- **立即处理**：DrugAgent active code 不应新增该前缀；从 owning project 目录运行。
- **长期修复**：另立代码任务评估 imported Slime 全树残留；本轮不改代码。
- **相关文档/入口**：已知问题、`scripts/check_repo.py`。状态：active DrugAgent mitigated，宽树仍残留。

## Root `PYTHONPATH` / Slime 运行目录

- **症状**：`drug_agent.*` 或 `molclaw_kg` import 失败。
- **典型日志片段**：`ModuleNotFoundError`。
- **根因**：Slime scripts 假设从 `slime/` 运行；Molclaw-KG 使用 `src` layout。
- **立即处理**：Slime 从 `slime/` 运行；未安装 KG 时使用 `PYTHONPATH=src`。
- **长期修复**：在入口文档维持运行目录，不引入 monorepo 包名前缀。
- **相关文档/入口**：入口目录、FAQ。

下一步应该读：[已知问题](../known-issues.md)  
如果要修改相关代码，请先读：[开发者指南](../developer-guide.md)
