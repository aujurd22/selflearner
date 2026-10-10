# 评估器自进化与元认知：方案来源引注

## 一、评估器自进化（三条路线，按落地成本排序）

### 路线 1：DynamicRubric — 评判标准根据 policy 改进而更新

**来源**：[Co-Evolving LLM Evaluators and Policies via DynamicRubric](https://arxiv.org/abs/2607.20083)
**核心**：policy 改进导致旧评分标准失去区分度 → 评估器生成新 rubric → 恢复区分能力。
**selflearner 落地**：novelty judge 分析自身误判模式 → 生成新评判规则 → 注入 judge prompt → 下一轮判别力提升。
**工程量**：低（judge 已是 LLM，加一步"分析+生成新规则"）。
**引注**：论文证明 evaluator score gap 是 policy 优化的核心信号；gap 塌缩时需要新 rubric 恢复。

### 路线 2：EvoRubrics — 对抗性协同进化

**来源**：[EvoRubrics: Dynamic Rubrics as Rewards via Adversarial Co-Evolution](https://arxiv.org/abs/2606.23038)
**核心**：rubric 生成器和 policy 对抗进化——rubric 不断提出 policy 无法"钻空子"的评判标准。
**selflearner 落地**：在路线 1 基础上，rubric 生成器从"修复误判"升级为"预防钻空子"。
**工程量**：中（需对抗训练循环，比路线 1 多一个生成器角色）。
**引注**：论文证明静态 rubric 在 policy 改进后出现 reward saturation 和 potential hacking。

### 路线 3：评估器可证伪性

**来源**：设计推断（基于 Popper 可证伪性原则），无直接论文先例。
**核心**：要求评估器给出可被后续经验推翻的理由，而非标量分数。如果后续证明理由不成立，评估器权重下降。
**selflearner 落地**：novelty judge 输出"我认为这个引理新颖，因为它连接了 A 和 B"→ 后续如果 A-B 连接被证伪，judge 的该条规则权重下降。
**工程量**：中高（需要跟踪评估器判断的下游验证结果，再反馈到评估器自身）。
**状态**：**无直接论文先例，但有五仓实测支撑**——intuition-mechanism 的四条件机械化检查（C/V/T/N）已经是这种"理由可验证"的设计，只是还没用于评估器权重的动态调整。

---

## 二、元认知缺失的具体做法

### 做法 1：双环学习架构

**来源**：
- **管理学原型**：Argyris & Schön, "Organizational Learning" (1978)——single-loop vs double-loop learning。
- **LLM 实例**：[Reflexion](https://arxiv.org/abs/2303.11366)（Shinn et al., 2023）——语言反馈作为 verbal RL。
- **LLM 实例**：[Learn Like Humans: Meta-cognitive Reflection](https://arxiv.org/abs/2601.11974)——MARS 框架，单循环内实现原则化反思。

**selflearner 落地**：
- 内环 = 现有 propose-check 循环（已运行）
- 外环 = 新增分析脚本：读 log.jsonl → 统计各域/类型通过率 → 生成策略修改建议
- 外环输出写入 `strategy.json` → 下一个 loop 的种子采样和 prompt 模板用新策略

### 做法 2：元认知重用（行为手册）

**来源**：[Metacognitive Reuse: Turning Recurring LLM Reasoning Into Concise Behaviors](https://arxiv.org/abs/2509.13237)
**核心**：将反复出现的推理片段压缩为简洁的 "behaviors"（名称+指令），存入行为手册，推理时注入上下文。
**selflearner 落地**：准入引理的证明策略（"用 omega 处理线性算术""用 ring 处理多项式恒等"）提炼为 behavior 条目存入手册，后续提议时按域匹配注入。
**工程量**：低（就是从 log 中提取模式 → 格式化为短指令 → 注入 prompt）。

### 做法 3：元认知整合（跨实例技能积累）

**来源**：[Beyond Meta-Reasoning: Metacognitive Consolidation](https://arxiv.org/abs/2604.17399)
**核心**：现有 meta-reasoning 是 episodic（单次任务内），缺少跨实例的可复用技能积累。Metacognitive Consolidation 在任务完成后提炼可复用的元推理技能。
**selflearner 落地**：每完成一个 loop，从日志中提炼"这个 loop 学到什么元推理技能"（如"组合拓扑引理时 simpa + exact 组合比 direct proof 成功率高"），写入技能库，后续 loop 注入。
**工程量**：中（需要跨 loop 的技能存储+检索+注入管线，但格式可复用 behavior handbook）。

### 做法 4：元认知奖励（校准模型）

**来源**：设计推断；理论基础为 [Knowing What LLMs Do Not Know](https://arxiv.org/abs/2401.13275)（校准 = 知道自己不知道什么）。
**核心**：给 Agent 额外奖励——"你能否预测自己下一步的学习效果？"
**selflearner 落地**：Agent 在提议前预测"这个候选有 X% 概率通过编译+三门"，预测与实际结果的校准度作为额外指标。校准好的 Agent 说明它对自己的能力边界有准确模型。
**工程量**：低（只需在 log 中加一列 predicted_probability，统计校准曲线）。

---

## 三、失败驱动的搜索空间缩减

**来源**：五仓实测（SL-60 零结果、hybrid v1-v6 锁死五版迭代、FlyLoop M6 不可判定）。**无直接论文先例——这是我们自己的最强实证规律。**

**核心**：每次失败都永久缩减了搜索空间（"知道了什么不行"）。实际发生的过程：
- SL-60：证明了弱提议器 0/60 → 确认瓶颈在提议器
- hybrid v1-v6：五版迭代逐步排除了"固定阈值""绝对置信""K=6 不触发"等方案
- FlyLoop M6：预注册门槛未达到 → 转向 M6b 新协议

**selflearner 落地**：将失败模式写入 `strategy.json` 的 `avoid` 字段，后续提议器的 prompt 中显式注入"避免清单"。

---

## 四、提出定义（从解题者到概念创造者）

**来源**：设计推断（基于 mathlib 社区的实际共识——重大 PR 往往引入新定义而非孤立定理）。无直接论文先例。

**selflearner 落地**：扩展提议器的 prompt，允许提议"新定义、新记号、新结构"而非仅新定理。评估标准：新定义能否简化现有证明（如"用这个定义，以下 3 个定理的证明缩短了 X 行"）。

**引注**：mathlib 的 `to_additive` 属性就是一个天然案例——乘法→加法的定义迁移自动化了大量证明。

---

## 来源汇总表

| 方案 | 来源类型 | 论文/实验引注 | 落地成本 |
|---|---|---|---|
| DynamicRubric 评估器进化 | 论文 | arXiv 2607.20083 | 低 |
| EvoRubrics 对抗协同进化 | 论文 | arXiv 2606.23038 | 中 |
| 评估器可证伪性 | 设计推断 | 无直接先例；五仓 C/V/T/N 是基础 | 中高 |
| 双环学习 | 管理学+论文 | Argyris & Schön 1978; Reflexion 2303.11366; MARS 2601.11974 | 低 |
| 元认知重用（行为手册） | 论文 | arXiv 2509.13237 | 低 |
| 元认知整合（跨实例技能） | 论文 | arXiv 2604.17399 | 中 |
| 元认知奖励（校准） | 设计推断 | Knowing What LLMs Don't Know 2401.13275 | 低 |
| 失败驱动搜索空间缩减 | **五仓实测** | SL-60 零结果; hybrid v1-v6; FlyLoop M6 | 零（已在做） |
| 提出定义 | 设计推断 | mathlib to_additive 惯例 | 中 |
