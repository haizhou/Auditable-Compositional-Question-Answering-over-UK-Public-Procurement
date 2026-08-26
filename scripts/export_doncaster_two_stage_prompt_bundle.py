#!/usr/bin/env python3
"""Export a two-stage teacher failure, repair, and replay bundle for Doncaster."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from procurement_graph.reasoning.graph_planning import (  # noqa: E402
    compile_graph_plan,
    execute_graph_plan,
    graph_execution_trace,
)
from procurement_graph.reasoning.kg_backend import RuntimeKGBackend  # noqa: E402
from procurement_graph.reasoning.schema_retrieval import retrieve_schema_context  # noqa: E402
from procurement_graph.reasoning.typed_planning import (  # noqa: E402
    _fastpath_veto,
    compile_typed_plan,
    graph_plan_schema,
    intent_program_schema,
    question_intent_program_messages,
    repair_graph_plan_schema,
    repair_understanding_messages,
    typed_plan_messages,
    typed_replan_messages,
)


CASE_ID = "L2::bridge_join_0155#L2a"
STEM = "doncaster_two_stage_teacher_prompt_bundle"


def read_case(path: Path) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("id")) == CASE_ID:
            return row
    raise KeyError(f"{CASE_ID} not found in {path}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    benchmark_path = ROOT / "data/qa/cicada_core_v4/train.jsonl"
    trace_path = ROOT / "data/qa/teacher_full_v1/traces.jsonl"
    hard_path = ROOT / "data/qa/teacher_full_v1/hard_negatives.jsonl"
    repair_path = ROOT / "data/qa/teacher_full_v1/repair_sft.jsonl"
    dpo_path = ROOT / "data/qa/teacher_full_v1/dpo_pairs.jsonl"
    prompt_source = ROOT / "src/procurement_graph/reasoning/typed_planning.py"
    feedback_source = ROOT / "scripts/eval_targeted_v2.py"
    runner_source = ROOT / "scripts/run_teacher.py"

    benchmark = read_case(benchmark_path)
    trace = read_case(trace_path)
    hard = read_case(hard_path)
    repair = read_case(repair_path)
    dpo = read_case(dpo_path)
    question = str(benchmark["question"])
    briefing = hard["step1_briefing"]
    rejected = hard["rejected_graph_plan"]
    accepted = repair["target_graph_plan"]
    schema_context = retrieve_schema_context(question)

    stage1_system, stage1_user = question_intent_program_messages(
        question, schema_context=schema_context
    )
    fast_candidate = compile_typed_plan(question, {"intent_program": briefing})
    fast_graph = getattr(getattr(fast_candidate, "graph_plan", None), "raw_graph_plan", None)
    veto_reasons = _fastpath_veto(question, fast_graph) if isinstance(fast_graph, dict) else []

    stage2_system, stage2_user = typed_plan_messages(
        question,
        understanding=briefing,
        schema_context=schema_context,
        variant="lean",
    )

    allowed_actions = [
        "fix_question_type",
        "repair_constraints",
        "swap_buyer_supplier",
        "change_operator",
        "change_operation",
        "abstain",
    ]
    full_repair_feedback = {
        "question": question,
        "selected_plan_id": "typed_count:p0",
        "failed_plan": {"graph_plan": rejected},
        "failure_stage": "verifier",
        "failure_reason": "wrong_answer",
        "submitted_answer": hard["answer"],
        "grounding_issues": [],
        "schema_errors": [],
        "failed_checks": [],
        "answer_sanity": {},
        "postflight_failed_checks": [],
        "deterministic_guards_added": [],
        "allowed_repair_actions": allowed_actions,
        "notes": [
            "The submitted answer did not match the hidden verifier.",
            "The reference/oracle answer is intentionally hidden from the reflector.",
            "Repair the plan using only the question and trace summary.",
        ],
    }
    reading_system, reading_user = repair_understanding_messages(
        question, full_repair_feedback
    )
    graph_feedback = {
        **full_repair_feedback,
        "retrieved_schema_context": schema_context,
    }
    repair_system, repair_user = typed_replan_messages(question, graph_feedback)

    backend = RuntimeKGBackend.from_directory(ROOT / "data/kg")
    accepted_plan, compile_reason = compile_graph_plan(
        question, accepted, org_resolver=backend.org_resolver()
    )
    if accepted_plan is None:
        raise RuntimeError(f"accepted graph did not compile: {compile_reason}")
    replay = graph_execution_trace(execute_graph_plan(backend, accepted_plan))
    replay_summary = {
        "status": replay.get("status"),
        "answer": replay.get("answer"),
        "execution_levels": replay.get("execution_levels"),
        "variables": [
            {
                "var_id": var.get("var_id"),
                "kind": var.get("kind"),
                "output_size": var.get("output_size"),
                "emitted_field": var.get("emitted_field"),
                "depends_on": var.get("depends_on"),
            }
            for var in replay.get("variables", [])
        ],
        "online_checks": (replay.get("low_level_result") or {}).get("checks", []),
    }

    bundle = {
        "case_id": CASE_ID,
        "question": question,
        "provenance_notice": {
            "historical_fact": (
                "The corpus preserves the parsed Stage-1 briefing, normalized rejected graph, "
                "submitted answer, oracle verdict, and accepted repair. It does not preserve the "
                "original provider request bytes, raw Stage-2 completion, or repair-reading "
                "completion for this row."
            ),
            "two_stage_routing_evidence": (
                "Under the committed teacher routing, the stored Stage-1 program compiles to a "
                "count over an entity_set. The semantic fast-path veto returns "
                "count_target_is_entity_set_for_record_question, so the configured lean Stage-2 "
                "planner prompt is invoked. The compact historical artifact lacks an explicit "
                "route tag, so this is a source-and-artifact reconstruction rather than a raw API "
                "transcript."
            ),
            "reconstruction_rule": (
                "All prompt messages and response schemas are emitted by the committed runtime "
                "builders from the stored question, briefing, rejected graph, and failure fields."
            ),
        },
        "models_and_settings": {
            "stage1_model": "gpt-5.4-nano",
            "stage2_and_graph_repair_model": "grok-4-1-fast-non-reasoning",
            "temperature": 0.0,
            "stage2_prompt_variant": "lean",
            "stage2_schema_variant": "optional",
            "configured_plan_samples": 2,
        },
        "teacher_call_1_stage1": {
            "evidence_status": "complete prompt reconstructed by committed builder",
            "model": "gpt-5.4-nano",
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": stage1_system},
                {"role": "user", "content": stage1_user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": intent_program_schema(),
            },
            "historical_parsed_response": briefing,
        },
        "stage1_fastpath_assessment": {
            "compiled_candidate": fast_graph,
            "candidate_status": getattr(fast_candidate, "status", ""),
            "semantic_veto_reasons": veto_reasons,
            "stage2_required_by_committed_route": bool(veto_reasons),
        },
        "teacher_call_2_stage2": {
            "evidence_status": (
                "complete lean prompt reconstructed by committed builder; historical raw provider "
                "completion was compacted to the normalized rejected graph"
            ),
            "model": "grok-4-1-fast-non-reasoning",
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": stage2_system},
                {"role": "user", "content": stage2_user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": graph_plan_schema("optional"),
            },
            "historical_normalized_response": rejected,
        },
        "initial_execution_and_offline_verdict": {
            "online_verified": trace["verified"],
            "submitted_answer": trace["answer"],
            "oracle_match": trace["oracle_match"],
            "hidden_oracle": trace["oracle"],
            "semantic_error": (
                "The graph stops at the buyer-local source side and an underspecified entity "
                "variable. It never binds the derived CPVs into a target procurement-record "
                "population, so it returns 1,137 rather than counting all matching notices."
            ),
        },
        "repair_teacher_call_1_reading": {
            "evidence_status": "complete input reconstructed from code and preserved failure fields",
            "model": "gpt-5.4-nano",
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": reading_system},
                {"role": "user", "content": reading_user},
            ],
            "response_format": "free text with eight labelled sections",
            "historical_model_response": None,
            "missing_reason": "run_teacher.py did not export the repair-reading completion",
        },
        "repair_teacher_call_2_graph": {
            "evidence_status": (
                "complete no-invention reconstruction from preserved fields; the historical "
                "request additionally contained the discarded repair-reading completion"
            ),
            "model": "grok-4-1-fast-non-reasoning",
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": repair_system},
                {"role": "user", "content": repair_user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": repair_graph_plan_schema("optional"),
            },
            "historical_accepted_repaired_graph": accepted,
        },
        "deterministic_replay_of_accepted_repair": replay_summary,
        "stored_preference_pair": {
            "chosen_graph_plan": dpo["chosen_graph_plan"],
            "rejected_graph_plan": dpo["rejected_graph_plan"],
            "pair_kind": dpo["pair_kind"],
        },
        "source_hashes": {
            str(benchmark_path.relative_to(ROOT)): sha256(benchmark_path),
            str(trace_path.relative_to(ROOT)): sha256(trace_path),
            str(hard_path.relative_to(ROOT)): sha256(hard_path),
            str(repair_path.relative_to(ROOT)): sha256(repair_path),
            str(dpo_path.relative_to(ROOT)): sha256(dpo_path),
            str(prompt_source.relative_to(ROOT)): sha256(prompt_source),
            str(feedback_source.relative_to(ROOT)): sha256(feedback_source),
            str(runner_source.relative_to(ROOT)): sha256(runner_source),
        },
    }

    out_dir = ROOT / "paper/tmlr_v4"
    json_path = out_dir / f"{STEM}.json"
    txt_path = out_dir / f"{STEM}.txt"
    json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sections = [
        "DONCASTER TWO-STAGE TEACHER FAILURE PROMPT BUNDLE",
        "=" * 80,
        json.dumps(bundle["provenance_notice"], ensure_ascii=False, indent=2),
        "\nTEACHER CALL 1: STAGE 1 SYSTEM\n" + "-" * 80,
        stage1_system,
        "\nTEACHER CALL 1: STAGE 1 USER\n" + "-" * 80,
        stage1_user,
        "\nTEACHER CALL 1: RESPONSE FORMAT\n" + "-" * 80,
        json.dumps(bundle["teacher_call_1_stage1"]["response_format"], ensure_ascii=False, indent=2),
        "\nHISTORICAL STAGE 1 RESPONSE\n" + "-" * 80,
        json.dumps(briefing, ensure_ascii=False, indent=2),
        "\nFAST-PATH ASSESSMENT AND VETO\n" + "-" * 80,
        json.dumps(bundle["stage1_fastpath_assessment"], ensure_ascii=False, indent=2),
        "\nTEACHER CALL 2: STAGE 2 SYSTEM\n" + "-" * 80,
        stage2_system,
        "\nTEACHER CALL 2: STAGE 2 USER\n" + "-" * 80,
        stage2_user,
        "\nTEACHER CALL 2: RESPONSE FORMAT\n" + "-" * 80,
        json.dumps(bundle["teacher_call_2_stage2"]["response_format"], ensure_ascii=False, indent=2),
        "\nHISTORICAL NORMALIZED STAGE 2 RESPONSE\n" + "-" * 80,
        json.dumps(rejected, ensure_ascii=False, indent=2),
        "\nINITIAL EXECUTION AND OFFLINE VERDICT\n" + "-" * 80,
        json.dumps(bundle["initial_execution_and_offline_verdict"], ensure_ascii=False, indent=2),
        "\nREPAIR READING CALL: SYSTEM\n" + "-" * 80,
        reading_system,
        "\nREPAIR READING CALL: USER\n" + "-" * 80,
        reading_user,
        "\nREPAIR GRAPH CALL: SYSTEM\n" + "-" * 80,
        repair_system,
        "\nREPAIR GRAPH CALL: USER\n" + "-" * 80,
        repair_user,
        "\nREPAIR GRAPH CALL: RESPONSE FORMAT\n" + "-" * 80,
        json.dumps(bundle["repair_teacher_call_2_graph"]["response_format"], ensure_ascii=False, indent=2),
        "\nHISTORICAL ACCEPTED REPAIR\n" + "-" * 80,
        json.dumps(accepted, ensure_ascii=False, indent=2),
        "\nDETERMINISTIC REPLAY SUMMARY\n" + "-" * 80,
        json.dumps(replay_summary, ensure_ascii=False, indent=2),
    ]
    txt_path.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(json_path)
    print(txt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
