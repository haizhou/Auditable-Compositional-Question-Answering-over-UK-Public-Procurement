# V4 Claim--Evidence Ledger

更新时间：2026-08-24

## 证据等级

- **A — 当前可复算**：当前代码/Parquet/JSONL 可直接重算，或完整测试可重跑。
- **B — 保存输出可审计**：逐项 prediction/trace 存在，但依赖外部 scorer、缺部分输入或缺完整 run manifest。
- **C — compact historical artifact**：只有 paper artifact、derived summary、hash 或工作日志；可作为 stored-artifact result，不能声称 current-HEAD reproduction。
- **D — 不应继续使用**：过期口径、协议混写、无 artifact 支撑或会造成因果误读。

## 数据与 KG

| Claim | Level | Evidence | 允许的写法 | 禁止扩张 |
|---|---|---|---|---|
| 166,277 source rows | C | `docs/ocds_data_analysis.md` | compiled releases in five annual files | unique OCIDs；当前可重算 |
| 215,221 contract-award nodes | A | `data/kg/nodes/contract_nodes.parquet` | award rows/nodes keyed by `(ocid, award_id)` | contracts in legal sense |
| 131,502 canonical org rows | A | entity/org Parquet | canonical organisation rows under stated ER conventions | verified legal entities |
| graph structural closure | A | current Parquet audit；`kg/validate.py` | no observed PK/endpoint/alias closure violations | real-world completeness/correctness |
| deterministic graph build | A | `kg/build.py` over frozen inputs | deterministic build over frozen resolved inputs | entire canonicalization is LLM-free |
| value additivity | A | `value_source`, `value_is_additive` | row-additive under fallback convention | realised GBP expenditure |
| record provenance | A | OCID/award/edge/evidence fields | queryable provenance and match scope | every pointer entails an award claim；trace always stores full population |

## Benchmark

| Claim | Level | Evidence | 允许的写法 | 禁止扩张 |
|---|---|---|---|---|
| 12,828 split total | A | `data/qa/cicada_core_v4/*.jsonl` | exact current split arithmetic | all rows independently hand-verified |
| 260 dev inside 2,285 | A | ID intersection | 2,025 non-development primary set | 2,285 independent sealed test |
| plan-level split gate | A | curation/diversification scripts + rows | construction applies plan-group isolation checks | no adaptive development contamination of 2,285 |
| 99.88% dual evaluator agreement | C | worklog + old thesis | documented 14,752/14,770 historical audit | current artifact-reproduced independent audit |
| all surfaces independently checked | D | Gate B sampling contradicts it | do not claim | — |

## Environment/runtime

| Claim | Level | Evidence | 允许的写法 | 禁止扩张 |
|---|---|---|---|---|
| conditional Step 2 | A | `typed_planning.py:2583-2680` | Step-1 typed intent with conditional graph planning | fixed reader->planner two-call runtime |
| deterministic replay | A | executor/graph code | same program + snapshot + conventions replay deterministically | same question alone always replays identically |
| exhaustive execution | A | preflight/executor/backend | aggregate plans require exhaustive access and execute over complete selected KG population | source data is complete reality |
| bounded repair | A | `pipeline.py`, `run_teacher.py` | eval max 1; harvest max 2; every repair re-executes | autonomous persistent self-improvement |
| online oracle-free | A | runtime routing/prompt sanitizer | no answer oracle in normal online control | no hidden evaluator anywhere in offline curation |
| layered verification | A | preflight/executor/postflight/sanity | checks have different authority | all checks are hard release gates |
| execution--faithfulness gap | A | 1,262 hard negatives | runtime pass does not imply oracle/shape correctness | oracle agreement proves constraint faithfulness |
| 7 types / 17 nodes | D for main runtime; A for compose | `compose/algebra.py` | use only for PACS/WTQ algebra, noting WTQ `extreme_rows` extension | procurement full-runtime action inventory |

## Training and repair

| Claim | Level | Evidence | 允许的写法 | 禁止扩张 |
|---|---|---|---|---|
| teacher routing counts | A | `teacher_full_v1/*.jsonl`, summary | 5,598 positives; 1,262 hard negatives; overlapping repair/DPO views | add all views as disjoint examples |
| 1,725 repair targets | A | `repair_sft.jsonl` | mostly compile/type/schema contract repair | mostly semantic answer repair |
| oracle-hidden offline repair | A | sanitizer + eval routing | only failure indication is exposed | repairer receives gold answer |
| formal exports | A | training `export_report.json` | report exact train/val pool counts | use older thesis counts |
| SFT improves both bases | C | compact development ladder artifact | stable cross-base checkpoint observation | matched causal ablation |
| RSFT/DPO improve monotonically | D | ladder contradicts it | later stages are non-monotonic/policy-dependent | recursive monotonic improvement |
| self-harvest is fully local | D | Step 1 remains cloud nano in r1 | local Step-2 self-harvest | fully autonomous local loop |

## Evaluation results

| Claim | Level | Evidence | 允许的写法 | 禁止扩张 |
|---|---|---|---|---|
| fully local Qwen 1,736/2,025 = 85.73% | C | `paper/tmlr_v3/artifacts/derived_metrics.json` | primary non-development stored-artifact result | current-HEAD end-to-end reproduction |
| teacher 1,401/2,025 = 69.19% | C | same | stored system comparison | pure model-quality causal contrast |
| top-40 RAG 778/2,025 = 38.42% | C | same | finite-retrieval system baseline on same items | retrieval-only matched ablation |
| plan-guided RAG 496/2,025 = 24.49% | C | same + baseline script | gold-constraint top-40 reader result | proof every retrieval design must fail |
| 70.4% untuned vs 31.5% RAG | D as controlled contrast | master table shows v2.2 vs v1 | historical context with protocol-version disclosure | clean computational-improvement estimate |
| grounding 89->103/136 | A | `paper/tmlr/grounding_impact.json` | fixed-plan additive-guard intervention | general feedback-repair effect；training causality |
| 56/229 constraint omissions | A | `paper/tmlr/grounding_training_signal.json` | boundary on targeted repair rows | population omission rate；56 个一定语义错误 |
| dev teacher 192/260 | C | third/best of three replicates | report as 73.9% replicate; mean 72.6%±1.1 preferred | sole stable teacher number |
| PACS 312/470/722/711 | C | corrected compact v1.1 artifact | corrected stored result with artifact-gap disclosure | use stale 332/450/687/675；fully sealed OOD benchmark |
| WTQ 978/1187/1930/2250 | B/C | saved predictions + official-score audit；targets missing | official evaluator results | internal JSON `correct` fields；current turnkey reproduction |

PACS decoding 仍是 unresolved protocol metadata：v3 method/runner 指向 prompt-only no-guided，旧 thesis ledger 指向 guided，而 raw JSONL 不保存 CLI args。在历史 command/log 恢复前，两种说法都不能进入 V4 的确定性 method 描述。

## V4 front matter 中已定位的待改项

| Current wording/idea | Status | Required correction |
|---|---|---|
| state is a versioned graph | unsupported as written | frozen procurement snapshot; add manifest before claiming versioned |
| procurement runtime has 7 types and 17 operators | wrong protocol | move to separate PACS/WTQ algebra description |
| learned reader and planner | imprecise | Step-1 typed intent program + conditional Step-2 graph planner |
| all syntax/.../release checks may trigger one repair | over-unified | distinguish hard preflight/execution failures, sanity repair/downgrade, and postflight disclosure |
| 70.4 vs 31.5 as computational comparison | protocol-confounded | disclose pipeline v2.2 vs v1 or remove from headline causal framing |
| grounding is local verification-feedback improvement | too broad | fixed-plan additive-sum grounding intervention |
| 166,277 canonicalised releases | needs scope | source file count is documented; snapshot unique count unavailable in checkout |
| provenance-preserving records | mostly valid | qualify capped trace evidence and OCID-fallback pointer semantics |
| benchmark independently audited at 99.88% | historical only | state as documented audit unless artifact is restored |

## 写作决策规则

1. Abstract 只使用能够在一两句中同时给出口径与限制的数字。
2. Main result 首先报告 2,025 non-development；2,285 放 appendix/continuity。
3. 将 improvement 拆成 system access/configuration、fixed-plan intervention、checkpoint change，不能用一个词暗示共同因果。
4. 把 PACS/WTQ 放在 separate protocol subsection，并明确没有 full runtime grounding/repair/evidence path。
5. 所有 oracle 相关动词优先用 filtering、agreement、curation、audit；避免 oracle gate 暗示在线 controller。
6. 对所有 C-level 结果使用 stored、audited、derived 或 historical 等限定，直到原始 artifact 恢复。
7. 不以“KG 是真世界”作贡献；贡献是 convention-explicit executable substrate 与 authority-separated measurement。
