# Training Methodology

适合读者：训练工程师、方法研究者、论文/汇报撰写者  
依赖文档：[数据生命周期](data-lifecycle.md)、[离线训练边界](../slime/drug_agent/OFFLINE_TRAINING_POLICY.md)  
相关入口：[训练 runbook](runbooks/training-sft-toolrl-gad.md)  
相关 contract：`react_sft`、`toolrl_step`、`gad_step`  
最后更新意图：用当前实现解释 SFT、ToolRL、GAD、OPD，不写通用 RLHF 教程

## 方法对比

| 方法 | 数据单位 | 训练目标 | 补充字段 | 负样本 | MCP | 主要入口 | 主要风险 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SFT | 完整 ReAct messages | teacher-forced `sft_loss` | 最小 SFT 正文 | 否 | 否 | SFT wrappers | 消息边界/loss mask、长样本 OOM |
| ToolRL | 单个 assistant decision 前的 fixed state | reference action rule reward + GRPO | label、metadata、target calls | 否 | 否 | ToolRL wrappers | state 切分或 action normalization 改变 reward |
| GAD Stage2 | ToolRL-style decision state | 冻结 student 生成 negative；BT warmup | teacher response、negative cache | 是 | 否 | GAD Stage2 scripts | negative/state 对齐错误 |
| GAD Stage3 | fixed state + current student group | discriminator + format/tool rule reward + GRPO | discriminator/version logs | 在线产生 | 否 | GAD Stage3 scripts | 服务版本、reward 组合、网络可达性 |
| OPD | fixed ToolRL-style state | frozen Megatron teacher KL + GRPO | teacher checkpoint | 否 | 否 | OPD wrappers | 相同 teacher/student 信号弱；成熟度有限 |

## 最小 ReAct 数据

`drug_agent_sft_react_json_v1` 正文包含 `schema_version`、`id`、`messages`。
消息中的 assistant 输出使用 `<thought>`、`<tool_call>`、`<final_answer>`，历史工具结果
作为 `<observation tool_name="...">`。SFT 直接消费完整 messages；`qwen3_5` loss mask
用于把训练 loss 对齐到 assistant 输出，避免把 user/observation 当作目标。

## 从一条 Trajectory 到三种视图

简化轨迹：

```text
user(question)
assistant(<thought>...</thought><tool_call>{"name":"dock","arguments":...}</tool_call>)
observation(tool result)
assistant(<final_answer>...</final_answer>)
```

- **SFT**：保留整条消息序列，学习两个 assistant turn。
- **ToolRL**：当前 converter 对含 MolClaw tool call 的 assistant turn建立样本；
  `prompt` 是该 turn 前的历史，reference action 存在 target/label/metadata。
- **GAD**：保留 tool-call 与 final-answer decision；每个样本只看到当前 decision 前的
  `state_messages`，teacher response 是正例，Stage2/current student 产生负例。

未来 observation 和当前 target response 都不能进入 decision state，否则会产生泄漏。

## ToolRL Offline Reward

ToolRL 从生成文本解析 MolClaw calls，与 reference tool calls 比较规范化工具名、参数名和
参数值，并组合格式与调用匹配得分。它评分的是文本/action，不通过 executor 获取新
observation。任何 reward 权重或 normalization 变化都属于行为变更，不应混入文档任务。

## GAD Stage2 与 Stage3

Stage2 从已有 SFT student checkpoint 生成当前 student negatives；actor 学习率为零，
reward 为零，输出 negative cache，再用 Bradley-Terry pairwise loss warm up 独立
discriminator。Stage3 由 current student 做 GRPO；discriminator 对 group 做
`/score-and-update`，默认总 reward 为：

```text
clip(0.8 * normalized_discriminator_score
   + 0.1 * format_reward
   + 0.1 * tool_schema_reward, -2, 2)
```

这是当前脚本/README 的默认实现，不是抽象建议。

## OPD 位置与成熟度

OPD 消费 fixed ToolRL-style states，以 frozen Megatron teacher KL 作为蒸馏信号并做
GRPO。当前默认相同 4B base teacher/student 适合验证链路，但初始蒸馏信号有限；
有意义实验需要兼容且更强的 teacher 或已有 student checkpoint。该路径的成熟度和实证
覆盖低于 SFT/ToolRL/GAD 主线。

## Offline / Online 边界

Formal SFT、ToolRL、GAD、OPD 都 source `offline_training_env.sh`，设置 offline 并禁用
tool env。student rollout 只表示生成下一 action；不会执行 action。真实 MCP 仅属于明确
命名的 online debug/evaluation utility。

下一步应该读：[训练 runbook](runbooks/training-sft-toolrl-gad.md)  
如果要修改相关代码，请先读：[开发者指南](developer-guide.md)
