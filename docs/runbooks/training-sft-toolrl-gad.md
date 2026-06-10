# Training SFT ToolRL GAD Runbook

适合读者：在正确 GPU worker 上准备和运行 formal training 的操作人员  
依赖文档：[训练方法](../training-methodology.md)、[离线训练边界](../../slime/drug_agent/OFFLINE_TRAINING_POLICY.md)  
相关入口：[入口目录](../entrypoints.md) 中所有 SFT/ToolRL/GAD/OPD training entrypoints  
相关 contract：`react_sft`、`toolrl_step`、`gad_step`  
最后更新意图：说明运行假设和安全检查；本文不会自动启动训练

## 共同假设

- 从 `slime/` 目录运行；保持 `drug_agent.*` import 语义。
- worker-local 环境脚本、`$SLIME`、`$VERL_DATA`、checkpoint、`/root/Megatron-LM` 存在。
- formal scripts source `offline_training_env.sh`，禁止 MCP/tool environment。
- 所有训练入口都会 `local-write` 且启动 Ray/GPU；GAD discriminator 还使用本地/可达 HTTP。

## 入口选择

| 任务 | 入口类别 | 说明 |
| --- | --- | --- |
| SFT 基础 smoke | `run_qwen3_5_0_8b_drug_sft_smoke.sh` | 参数化 SFT launcher |
| SFT 4B smoke/full | 4B SFT wrappers | TP=4 保守配置；full 使用 epoch-only |
| ToolRL smoke/full | ToolRL wrappers | 先生成并验证 step-level JSONL |
| GAD smoke | prepare -> Stage2 negatives -> discriminator warmup/service -> Stage3 smoke | 需要已有 SFT student |
| OPD | OPD wrappers | 当前主要用于链路验证/兼容 teacher 实验 |

具体状态、副作用和脚本路径以入口目录为准。

## Batch / Parallel 约束

- SFT smoke：`RBS >= GBS`，`RBS % GBS == 0`。
- SFT/ToolRL：`NUM_GPUS % (TP*PP*CP*EP) == 0`，`GBS % DP == 0`。
- ToolRL/GAD/OPD group sampling：`RBS * N_SAMPLES >= GBS` 且可整除 GBS。
- 4B SFT smoke 默认 TP=4、DP=1、RBS=GBS=1；full 默认 RBS=GBS=4。
- SFT 使用 `--loss-mask-type qwen3_5`。

## 训练前非侵入式 Checklist

1. 阅读入口脚本，确认其默认路径和将要写入的目录。
2. 静态确认 data、model、torch_dist checkpoint 和 resume marker 路径。
3. 对 SFT/ToolRL/GAD 输入运行对应 validator/转换报告检查。
4. 确认 offline policy、无 MolClaw credentials、无误继承 `expandable_segments`。
5. 核对 GPU 拓扑、batch/parallel 整除约束、磁盘和 host RAM。

不要在开发机通过执行训练脚本来“检查是否存在”；这些脚本会清理/启动 Ray 和 GPU 服务。

## 训练后检查

检查 Ray submit/full error logs、训练 loss/reward components、rollout/step 数、save dir、
checkpoint marker、GAD discriminator pre/post version 和 negative/cache 报告。Formal
training 中若出现 MCP 调用，应立即视为边界违规调查。

下一步应该读：[环境与资源](environment-and-resources.md)  
如果要修改相关代码，请先读：[开发者指南](../developer-guide.md)
