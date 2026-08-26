# 项目事实模型（写作前审计版）

更新时间：2026-08-24

本文档不是论文草稿，而是论文写作的事实底座。发生冲突时，证据优先级为：当前代码与可直接读取的 artifact > 保存的逐项评测输出 > 保存的汇总与 hash > 工作日志/旧论文叙述。不能被当前 checkout 重算的结果必须标为 stored-artifact result，不能写成 current-HEAD reproduction。

## 1. 项目究竟在做什么

一句话定义：

> 本项目把冻结的英国公共采购数据构造成一个约定显式、结构验证的 reasoning substrate，使 agent 提出的程序能够被 grounding、执行、重放和分层检查；它再利用这些可观察的执行结果研究有限在线修复与离线监督，而不是声称实现了自主 recursive self-improvement。

项目的真正研究对象不是“KG 能否提高 QA”，也不是“verifier 是否证明答案正确”，而是：在现实组合数据推理中，如何把 proposal、execution consequence、feedback authority 和 learning selection 变成可测对象，并明确 verification 看得见什么、看不见什么。

端到端链路为：

```text
UK OCDS compiled releases (2022--2026)
  -> latest-release snapshot per OCID
  -> tiered organisation resolution
  -> snapshot-aligned award/text extraction
  -> typed Parquet nodes and edges
  -> program-first QA instrument
  -> conditional typed-planning runtime
  -> grounding + exhaustive deterministic execution
  -> online structural feedback / abstention / bounded repair
  -> offline oracle and answer-shape curation
  -> SFT / self-harvest / preference checkpoints
  -> procurement evaluation + separate PACS/WTQ algebra protocols
```

## 2. 数据与 KG 构建

### 2.1 输入与 snapshot

- 来源是 UK Open Contracting Data publication 41 的五个年度 `JSONL.gz` compiled-release 文件，覆盖 2022--2026；2026 是部分年度。
- 文档记录 166,277 条 compiled releases：24,431 / 24,009 / 25,950 / 52,398 / 39,489。当前 checkout 缺 `data/raw/` 与 `data/interim/releases.parquet`，所以该数是文档来源，不能在当前仓库重新计算 unique-OCID 口径。
- ingest 丢弃缺 `ocid` 或 `date` 的记录，并为每个 OCID 保留日期最新的 release snapshot。
- rich extraction 再读 raw release，但必须同时匹配 winning `(ocid, release_id)`；这保证 extraction 与选定 snapshot 一致，而不是按文件顺序猜测。

主要入口：

- `pipelines/01_ingest.py`
- `src/procurement_graph/ingest/loader.py`
- `pipelines/04_extract.py`
- `src/procurement_graph/extract/tables.py`

### 2.2 组织消歧不是单一规则

实体解析按多个 tier 进行：

1. trusted registry identifiers；
2. 同一 OCID、同一 normalized name、共享 role 且唯一指向同一 official entity 的 GB-FTS cross-reference；
3. curated government-name lookup；
4. exact normalized `(name, region)` merge；
5. 无 region evidence 时的 name-only merge；
6. residual provisional singleton；
7. 后处理 safe-merge extension：deterministic 或 LLM-adjudicated candidate edge 只有在 component-level official-ID conflict 与 negative-edge conflict 检查后才应用。

因此：

- 131,502 是 canonical rows，不是经法律注册表验证的 legal entities。
- GB-FTS 不被当作权威 identity，但 unresolved singleton 可以保留 GB-FTS 作为 provisional node key；当前有 76,194 个这种 singleton key。
- KG table build 对冻结的 entity inputs 是 deterministic 的，但完整 canonicalization 过程不是“完全无 LLM”：最终 artifact 中有 255 个 `llm_safe_merge` rows。
- 当前仓库缺 safe-edge、LLM decision 和 conflict artifacts，无法从 candidate edge 级别完整重放 safe merge。

主要入口：

- `src/procurement_graph/er/phase1.py`
- `src/procurement_graph/er/phase2.py`
- `scripts/analyse_er_llm_decisions.py`
- `scripts/apply_safe_er_merges.py`

### 2.3 award 与金额语义

- 一个 contract-award node 对应 `(ocid, award_id)`，ID 为 `contract:{ocid}:{award_id}`。
- 金额 precedence 是 `award.value -> first matching contract.value -> tender.value -> missing`。
- `amount=0` 是合法值，不触发 fallback。
- 只有来源为 award 或 contract 的值被标为 `value_is_additive=True`；这只是 row-additive convention，不等于 realised expenditure。
- 当前 176,002 个 additive rows 中有 1,059 个非 GBP。组织/CPV enrichment 目前没有按 currency 分组或汇率换算，因此跨币种总和不能称为 GBP expenditure。
- 一个 award 有多个 matching contracts 时只取第一个 matching contract；这是确定性约定，不是完整 contract multiplicity model。

### 2.4 当前可直接审计的 graph artifact

| Artifact | 当前事实 |
|---|---:|
| raw aliases | 204,711 |
| canonical organisation rows | 131,502 |
| contract-award nodes | 215,221；涉及 118,088 个有 award 的 OCID |
| CPV nodes | 3,870 |
| evidence nodes | 535,731；覆盖 166,257 个 OCID |
| buyer edges | 215,218 |
| supplier edges | 334,063；覆盖 204,186 个 award nodes |
| category edges | 164,691 |
| evidence edges | 1,326,240；覆盖 215,202 个 award nodes |

当前 artifact 重新审计结果：所有 node/edge primary-key duplicates、`(ocid, award_id)` duplicates、alias target misses 和 edge endpoint misses 均为 0；additivity label consistency 也无 violation。历史 graph validation 为 23 PASS / 3 coverage WARN / 0 FAIL。

这些检查保证 structural closure，不保证现实世界语义完整。缺 supplier、CPV 或 evidence 的数据仍保持缺失，不被填造。

### 2.5 provenance 的准确含义

- structured records 保存 OCID、award ID、edge source 与金额来源。
- long text 保存 field path 与 lot ID。
- evidence link 优先 lot match；无法匹配 lot 时会回退到同 OCID 的全部 awards，并记录 `match_scope=ocid_fallback`。
- 因而 evidence pointer 可被追踪，但不自动构成 award-specific entailment。
- 大 population 的 answer/count 可以精确计算，但 trace 中保存的 evidence IDs/rows 可能 capped；“record-level provenance”不能误写成每次都保存完整 population。

## 3. Benchmark instrument

### 3.1 最终 benchmark 不是早期 Stage-1 builder 的直接输出

`pipelines/50--64` 描述的是早期 program-first builder：从 KG 抽 `AnswerSpec`，用独立 completeness index 重新导出 matched IDs，以 deterministic executor 产生 oracle，再生成/检查 surface。

最终 12,828-row instrument 还经历了：L1 cleaning、targeted-v2 扩展、L2 persona surfaces、mechanical faithfulness checks、gold backfill、contrast twins、plan-group split、curation/rebalancing、surface diversification、independent oracle evaluation 与最后的表面修正。

最终 split arithmetic 可由当前文件直接重算：

| Split | Rows |
|---|---:|
| train | 9,267 |
| dev_tune | 556 |
| dev_select | 671 |
| dev_smoke | 49 |
| final_test artifact | 2,285 |
| total | 12,828 |

其中 `compare_set_v4` 的 260 个开发/模型选择问题全部包含在 2,285-row `final_test` artifact 内。论文主结果必须去除这 260 个 ID，报告 2,025 个 non-development questions；2,285 只能作为 inclusive/continuity score，不能称为独立 sealed test。

### 3.2 oracle 与 surface audit 的边界

- independent evaluator 不 import reasoning/generation code，工作日志记录其与 construction evaluator 在 14,770 cases 中 agreement 14,752（99.88%）。当前 checkout 没有保存该逐项 audit artifact，所以这是 documented historical evidence，不是当前可复算 artifact。
- 该 agreement 验证 answer oracle conventions，不等于每个 natural-language surface 都经过独立语义审查。
- 早期 factoid Gate B 默认只抽样 30%；未抽中的表面会被流程标记 verified。后续机械/独立检查降低风险，但不能写成“所有 surface 均由独立 LLM checker 审核”。

## 4. 主采购 reasoning environment

### 4.1 environment contract 的实际映射

论文可将 environment 描述为：

| Environment component | 本项目中的对象 |
|---|---|
| state | 冻结的 resolved procurement snapshot、schema 与 executor conventions |
| action | `RuntimeQuerySpec` 或 typed graph/decomposition plan |
| transition | grounding 后的 deterministic query/graph execution |
| observation | execution status、intermediate variable populations、checks、capped evidence 与 answer card |
| feedback | 在线 structural/runtime signals；离线 oracle/shape labels；另行 constraint-faithfulness audit |

Replay 的准确条件是固定 `program + snapshot + executor/convention version`。只固定 question 不能保证 replay，因为 LLM planning 本身不是 deterministic environment transition。

“versioned graph”目前证据不足；更准确的词是 frozen snapshot 或 frozen artifact。若论文要写 versioned，必须补明确 snapshot/version manifest。

### 4.2 在线控制流

真实在线路径是：

```text
question + keyword-retrieved schema context
  -> Step-1 typed intent program
  -> if deterministically compilable and no fast-path veto:
       deterministic intent compiler (skip Step 2)
     else:
       conditional Step-2 graph planning
       structural resampling only after detectable compile/consistency defects
  -> consistency / compile
  -> schema and entity grounding
  -> exact-filter retrieval
  -> preflight
  -> deterministic single-query, graph, or decomposition execution
  -> evidence verdict + postflight disclosure + answer sanity
  -> answer or abstention
  -> eligible structured failure may trigger bounded replan
```

因此不能写成每题固定的“reader -> planner”两次 LLM。Step 2 是 conditional fast-path fallback。

在线 evaluation 默认最多 1 个 feedback replan；teacher harvest 为提高数据 yield 最多 2 个。每次 repair 都重新走 compile/ground/execute/check，reflector 不认证自己的修复。

clean `no_results` 不重规划，以避免 answer shopping。repair prompt 会删除 oracle/reference/gold/expected-answer 字段。

### 4.3 verifier 的 authority 不是单一 gate

在线可以检查：

- schema/typing/operation contract；
- grounding confidence 与 constraint conflict；
- exhaustive flag；
- execution status；
- non-empty/multiplicity/additivity 等执行条件；
- evidence、population-coverage disclosure 与 answer sanity。

但当前代码在 `result.passed` 后构造 answer card；postflight failure 主要形成 disclosure，sanity failure可触发 repair或降级，而 repair 失败时原答案可能保留。因此不能把所有 postflight/sanity 项统一称为 hard release gates。

在线 verifier 看不见一般意义上的 executable-but-wrong。训练 harvest 中有 1,262 个 runtime-pass 但被 offline oracle/shape 拒绝的 hard negatives，这正是 execution--faithfulness gap 的直接证据。

### 4.4 主 runtime 与 recursive algebra 是两套协议

主采购 full runtime 使用：

- `TypedLLMPlanner`
- `RuntimeQuerySpec` / graph plan / decomposition
- `ReasoningPipeline`
- grounding、preflight、exhaustive execution、answer card 与 bounded repair

PACS/WTQ 使用另一套 single-call recursive tree algebra：

```text
question (+ table schema for WTQ)
  -> one model call
  -> recursive JSON tree or abstention
  -> validate_tree
  -> direct algebra evaluator
  -> offline denotation score
```

七种 return types 与原始 17 个 node types属于第二套 compose algebra，不属于主采购 runtime。当前 WTQ 代码还增加了 `extreme_rows`；准确写法是“seven-type algebra with seventeen original nodes, extended on WTQ by a row-preserving arg-extremum node”。

主 runtime 的 planner-facing operation units 是 11 个（含 abstain），single-query executor 支持 10 个 operations；compare/bridge 由 graph/decomposition path 实现。

## 5. Offline curation 与 learning

### 5.1 teacher harvest 的真实 routing

输入：9,267 train questions，其中 8,555 answerable、712 unanswerable。

真实池：

| Outcome/view | Count |
|---|---:|
| answer-producing runtime-pass traces | 6,860 |
| runtime-pass and oracle-match | 5,605 |
| direct positive graph targets after shape check | 5,598 |
| hard negatives | 1,262 = 1,021 oracle mismatch + 241 shape mismatch |
| abstention targets | 590 |
| repair targets | 1,725 |
| preference pairs | 390 |
| answerable failures | 1,789 |

`6,860 = 5,598 positives + 1,262 hard negatives`。repair 与 DPO 是重叠 supervision views，不能再与 positives 相加成“独立训练样本总数”。

在线 runtime 无 answer oracle。offline harvest 才加入 expected-status、hidden oracle agreement 与 answer-shape checks。对错误答案的 repair feedback 只说 failed external validation，不把正确答案交给 repairer。

### 5.2 repair 数据主要修什么

1,725 个 repair targets 按 failure stage：

| Stage | Count |
|---|---:|
| plan_compile | 1,340 |
| external_validation（offline） | 242 |
| executor | 125 |
| schema | 17 |
| graph_executor | 1 |

约 78% 在读取数据记录前已经失败。因此主要 learning signal 是程序契约、typing、schema/grounding 与结构修复，不是 verifier 对最终语义错误的全面纠正。

### 5.3 正式 training exports

- Round-1 plan SFT：2,787 train + 57 validation；plan pool 含 258 个 capped abstention examples。
- Round-1 repair SFT：1,679 + 46。
- teacher DPO：390 pairs。
- Step-1 distillation：5,091 + 96；来源为 4,479 teacher、463 Qwen r1、245 Llama r1，且必须有正确 outcome 与合法 intent-program shape。
- RSFT Qwen：3,019+65 plan，3,169+79 repair。
- RSFT Llama：3,026+66 plan，3,190+80 repair。
- DPO Qwen：1,079 = 390 teacher + 689 on-policy。
- DPO Llama：1,083 = 390 teacher + 693 on-policy。

RSFT self-harvest 的 Step 1 仍使用 cloud nano，只有 Step 2 是本地 SFT student，所以它不等于 fully local self-improvement。

## 6. 实验协议与能回答的问题

| Protocol | 数据/规模 | 实际回答的问题 | 不能回答的问题 |
|---|---:|---|---|
| procurement non-development | 2,025 | 完整 system configurations 在现实组合采购任务上的效果 | 单组件因果；独立于全部开发决策的 sealed test |
| inclusive procurement | 2,285 | 与历史结果连续比较 | 独立 confirmatory score |
| checkpoint ladder | 260，13 buckets x 20 | 同一开发问题上保存 checkpoint 的阶段变化 | 匹配数据量/目标/随机种子的 component ablation |
| fixed-plan grounding replay | 136 with oracle | grounding transformation 对固定计划的窄 counterfactual | training gain 的因果来源；一般 structured feedback 效果 |
| constraint-retention audit | 229 targeted repair targets | oracle/runtime acceptance 与 faithfulness 可分离 | 全体遗漏率估计 |
| PACS v1.1 | 922 | single-call recursive algebra 的组合性与表面敏感性 | full runtime、grounding 或 repair 的 ablation |
| WTQ official | 4,344 / 421 unseen tables | typed algebra planning 跨到表格的 portability | procurement environment 整体迁移；单变量 supervision ablation |

## 7. 当前可信结果轮廓

### 7.1 主采购 non-development（2,025）

| System | Correct | Accuracy |
|---|---:|---:|
| closed-book | 317 | 15.65% |
| plan-guided top-40 retrieval | 496 | 24.49% |
| top-40 RAG | 778 | 38.42% |
| cloud teacher runtime | 1,401 | 69.19% |
| hybrid Llama | 1,527 | 75.41% |
| hybrid Qwen | 1,574 | 77.73% |
| fully local Llama | 1,681 | 83.01% |
| fully local Qwen | 1,736 | 85.73% |

fully local Qwen 在 1,725 个 answerable 中 1,436 correct，在 300 个 non-answerable 中 300 correct。上述结果来自保存的 derived artifact；原始 final run directories 在本工作区缺失，因此属于 stored-artifact results。

保存预测上的 paired re-score 给出：fully local Qwen vs cloud teacher 为 +372/-37（exact McNemar `p=9.79e-71`），vs hybrid Qwen 为 +222/-60（`p=5.005e-23`）。这些检验排除了同一批 item 上的简单 sampling fluctuation，但不测训练 seed、provider 或 serving-stack 方差。

### 7.2 260-question development checkpoint ladder

- Qwen：untuned 183、SFT 211、RSFT 212、DPO 217。
- Llama：untuned 156、SFT 216、RSFT 215、DPO 201。
- SFT 是唯一在两种 base 上都改善的阶段；RSFT 近乎中性；DPO 在 Qwen 上提高、在 Llama 上明显下降。因此不能写 monotonic improvement。
- cloud teacher 同配置三次为 71.9%、71.9%、73.9%，均值 72.6%±1.1。192/260=73.85% 是其中最佳/第三次，若使用必须明确 replicate，不应伪装为唯一稳定分数。
- 70.4% untuned Qwen（pipeline v2.2）与 31.5% RAG naive（pipeline v1）不是严格同版本控制对比。它们可作历史背景，不能作为 clean causal estimate。主 2,025 系统表提供更一致的数据集比较，但仍是 system-level comparison。

### 7.3 verification boundary

- fixed-plan grounding：89/136 correct before，103/136 after；14 wrong-to-correct，0 correct-to-wrong，另 1 newly executable but still wrong。14 个 rescue 都来自 additive-sum guard，不能概括成一般 feedback repair。
- 229 个机械可审计 repair targets：173 保留全部 mapped constraints，56 被标记遗漏。该 audit 是 targeted subset，不是总体 omission prevalence。

### 7.4 PACS 与 WTQ

PACS corrected v1.1（n=922 = 730 answerable + 138 unsupported + 54 no-result）：base-A 312、teacher-A 470、Compose-v3-A 722、Compose-v3-B 711。旧 summary 仍含过期的 332/450/687/675；corrected per-item 与 status-transform script 当前缺失，因此这些是审计后的 compact stored results。

PACS 的最安全定位是 frozen one-shot compositional diagnostic，而不是 fully sealed OOD benchmark：seal code 有 exact question/tree checks，但没有独立 G3 template-identity gate，lexical G5 也只抽样每七个 training trigram set。另有历史协议冲突：TMLR v3/runner 写 prompt-only、no guided，旧 thesis ledger 写 guided，而 raw output 不保存 CLI args；找到历史 command/log 前，V4 不应断言 guided 或 unguided。

WTQ official scorer（n=4,344，421 unseen tables）：base 978、procurement Compose-v3 1,187、answer-only A 1,930、translated-gold C 2,250。official paired transitions 分别为 +387/-178、+833/-90、+628/-308。必须使用 official evaluator重算结果，不能使用保存 JSON 的内部 `correct` 字段。C-final 约 5,423-row training snapshot 与 CoreNLP tagged targets 当前不在 repo。pristine test 消费后的 compiler/coverage 实验只能称 post-hoc diagnostic，不能替换 headline。

## 8. 可重现性现状

已验证：

- 当前代码完整测试：483/483 passed（2026-08-24，在沙箱外运行以绕过 Windows tempfile 权限伪失败）。
- 当前 entity/KG Parquet 的计数、主键、alias closure、edge endpoint closure 与 additivity consistency 可直接审计。
- 当前 benchmark split、teacher pool 与主要 training export counts 可直接读取。
- WTQ 四组 4,344-row predictions 存在，可按 official scorer 协议审计，但 tagged targets 缺失。

不能在当前 checkout turnkey 重现：

- raw -> interim -> extracted -> KG 全链路，因为 raw/interim/extracted 与 graph validation report 缺失；
- safe-merge candidate/decision/conflict chain；
- procurement final runs 与 checkpoint ladder 的完整逐项输出/command/checkpoint manifest；`outputs` 只是指向 Linux 路径的 30-byte pointer；
- PACS v1.1 corrected per-item transformation；
- WTQ C-final training snapshot；
- 14,770-case independent oracle audit 的逐项结果。

## 9. 对 V4 写作的直接约束

必须改：

1. 把主 procurement runtime 与 PACS/WTQ recursive algebra 分开。
2. 把固定 two-stage 改成 Step-1 intent program + conditional Step-2 graph planning。
3. 把 “versioned graph” 改成 frozen snapshot，除非补 version manifest。
4. 不把 postflight/sanity 全称为 hard release gates。
5. 不把 execution pass、oracle agreement 或 evidence pointer写成 semantic-faithfulness certificate。
6. 不把 2,285 称为独立 sealed test；headline 使用 2,025 non-development。
7. 不把 14 grounding rescues 写成一般 verification feedback 的效果，它是 additive guard 的窄 intervention。
8. 不把 checkpoint ladder 写成 monotonic learning 或 component ablation。
9. 不把 131,502 写成 verified organisations，也不把 additive values 写成 realised GBP spend。
10. 所有结果按 artifact tier 标注，尤其 PACS corrected、procurement final runs 与 99.88% agreement。

仍然成立的论文主轴：

> The environment does not create or certify improvement; it makes proposed reasoning actions, their executable consequences, and feedback pathways observable enough to locate gains and verification boundaries.

但更准确的 operational 定义应是：

> The procurement environment exposes a conditional typed-planning runtime with deterministic grounding, exhaustive graph execution, structured failures, and bounded oracle-free repair. A separate closed recursive algebra probes direct compositional planning on PACS and WikiTableQuestions. Offline curation adds oracle and answer-shape filtering without exposing oracle content to the planner or repairer.
