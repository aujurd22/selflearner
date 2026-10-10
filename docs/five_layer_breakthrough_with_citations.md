# 五层突破框架：逐层来源引注与 selflearner 可落地方案

每项方案标注来源类型（论文/五仓实测/设计推断）+ arXiv 引注（如有）+ selflearner 落地方式。

---

## 第一层：评估器与学习者共同进化

### 1a. DynamicRubric（评判标准动态更新）

**论文**：[Co-Evolving LLM Evaluators and Policies via DynamicRubric](https://arxiv.org/abs/2607.20083)
**核心**：policy 改进导致旧评分标准失去区分度 → 评估器生成新 rubric → 恢复区分能力。
**selflearner 落地**：novelty judge 分析自身误判模式 → 生成新评判规则 → 注入 judge prompt。
**成本**：低。

### 1b. EvoRubrics（对抗性协同进化）

**论文**：[EvoRubrics](https://arxiv.org/abs/2606.23038)
**核心**：rubric 生成器与 policy 对抗进化，rubric 不断提出 policy 无法"钻空子"的评判标准。
**selflearner 落地**：路线 1 跑通后的升级方向。
**成本**：中。

### 1c. SkillForge（技能生命周期管理）

**论文**：[SkillForge: Co-Evolving Skills and Agents via Dynamic Skill Lifecycles](https://arxiv.org/abs/2610.09832)
**核心**：技能库通过 trial/active/stable/retired 四态生命周期管理，技能与模型共同进化。
**selflearner 落地**：准入引理的证明策略条目按四态管理——新策略先"trial"（低权重使用），有正向证据后升级"active"，长期稳定后"stable"，被更优策略替代后"retired"。
**成本**：中。

---

## 第二层：自动课程学习 + 内在动机

### 2a. Absolute Zero Reasoner（无外部数据自博弈）

**论文**：[Absolute Zero: Reinforced Self-play Reasoning with Zero Data](https://arxiv.org/abs/2505.03335)
**核心**：提议器与求解器自博弈——提议器生成"对当前求解器最难但可解"的问题，求解器解决后双方共同进化。零外部数据。
**selflearner 落地**：从现有 181k 库中让 Agent 自己生成"最接近库边界的新引理"作为下一轮目标——不需要外部指定方向。
**引注**：AZR 已证明在代码/数学域有效；我们把它映射到 Lean/mathlib。

### 2b. 内在动机 = 压缩进度

**来源**：设计推断（基于 Schmidhuber 的压缩进度理论）。
**selflearner 落地**：内在奖励 = "准入的新引理能否缩短现有证明"（用 Lean 的 tactic 行数对比）。
**引注**：Schmidhuber, "Driving the Compression Progress" (2008)；Hutter, "Universal AI"。

---

## 第三层：元认知（双环学习 + 技能积累 + 校准）

### 3a. 双环学习（外环策略自适应）

**来源**：
- 管理学原型：Argyris & Schön, "Organizational Learning" (1978)
- LLM 实例：[Reflexion](https://arxiv.org/abs/2303.11366)（Shinn et al., 2023）
- LLM 实例：[MARS: Meta-cognitive Agent Reflective Self-improvement](https://arxiv.org/abs/2601.11974)

**selflearner 落地**：`evolve.py --analyze` 已实现（真实日志验证通过——3 个低通过率域+2 条 judge 规则演进建议）。外环输出写入 `strategy.json`，下一 loop 生效。

### 3b. 元认知重用（行为手册）

**论文**：[Metacognitive Reuse](https://arxiv.org/abs/2509.13237)
**核心**：将反复出现的推理片段压缩为简洁的 "behaviors"（名称+指令），存入行为手册，推理时注入上下文。
**selflearner 落地**：准入引理的证明策略（"用 omega 处理线性算术""用 ring 处理多项式恒等"）提炼为 behavior 条目存入手册，后续提议时按域匹配注入。

### 3c. 元认知整合（跨实例技能积累）

**论文**：[Beyond Meta-Reasoning: Metacognitive Consolidation](https://arxiv.org/abs/2604.17399)
**核心**：现有 meta-reasoning 是 episodic（单次任务内），缺少跨实例的可复用技能积累。
**selflearner 落地**：每完成一个 loop，提炼"这个 loop 学到什么元推理技能"写入技能库，后续 loop 注入。

### 3d. 元认知奖励（校准模型）

**来源**：设计推断；理论基础为 [Knowing What LLMs Do Not Know](https://arxiv.org/abs/2401.13275)。
**selflearner 落地**：Agent 在提议前预测"这个候选有 X% 概率通过编译+三门"，校准度作为额外指标。

---

## 第四层：失败驱动的搜索空间缩减（我们最强实证）

**来源**：五仓实测。**无直接论文先例——这是我们自己的最强实证规律。**

**证据**：
- SL-60：弱提议器 0/60 → 确认瓶颈在提议器
- hybrid v1-v6：五版迭代逐步排除方案
- FlyLoop M6：预注册门槛未达到 → 转向新协议

**selflearner 落地**：失败模式写入 `strategy.json` 的 `avoid` 字段，提议器 prompt 中显式注入"避免清单"。

---

## 第五层：提出定义（从解题者到概念创造者）

**来源**：设计推断；mathlib `to_additive` 惯例为天然案例。
**selflearner 落地**：扩展提议器 prompt 允许提议新定义/新结构；评估标准 = "用这个定义，以下 N 个现有定理的证明缩短了 X 行"。
**引注**：mathlib 的 `to_additive` 属性自动化了大量乘法→加法证明迁移。

---

## 来源汇总表

| 层 | 方案 | 来源 | 引注 | selflearner 落地状态 |
|---|---|---|---|---|
| 1a | DynamicRubric | 论文 2607.20083 | ✅ | 可实现（低） |
| 1b | EvoRubrics | 论文 2606.23038 | ✅ | 可实现（中） |
| 1c | SkillForge 生命周期 | 论文 2610.09832 | ✅ | 可实现（中） |
| 2a | Absolute Zero Reasoner | 论文 2505.03335 | ✅ | 可实现（中） |
| 2b | 压缩进度内在动机 | 设计推断 | Schmidhuber 2008 | 可实现（中） |
| 3a | 双环学习 | 管理学+论文 | Reflexion 2303.11366; MARS 2601.11974 | **✅ 已实现**（evolve.py） |
| 3b | 行为手册 | 论文 2509.13237 | ✅ | 可实现（低） |
| 3c | 元认知整合 | 论文 2604.17399 | ✅ | 可实现（中） |
| 3d | 元认知奖励（校准） | 设计推断 | 2401.13275 | 可实现（低） |
| 4 | 失败驱动搜索空间缩减 | **五仓实测** | 无外部先例 | **✅ 已在执行** |
| 5 | 提出定义 | 设计推断 | mathlib to_additive | 可实现（中） |
