"""
ClearNote summarization eval harness.

Usage:
    python eval/run_eval.py                  # run all cases
    python eval/run_eval.py --case case_004  # run one case by id
    python eval/run_eval.py --out results.json

Reads OPENAI_API_KEY from the root .env file automatically.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Allow running from repo root or from backend/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env from repo root before importing app config
from dotenv import load_dotenv  # type: ignore

load_dotenv(ROOT.parent / ".env")

from app.services.ai import AIService  # noqa: E402

CASES_PATH = Path(__file__).with_name("cases.json")


def load_cases(filter_id: str | None = None) -> list[dict]:
    with open(CASES_PATH) as f:
        cases = json.load(f)
    if filter_id:
        cases = [c for c in cases if c["id"] == filter_id]
    return cases


def run_case(ai: AIService, case: dict, retry: int = 2) -> dict:
    for attempt in range(retry + 1):
        try:
            actual = ai.summarize_notes(case["transcript"])
            return {"id": case["id"], "scenario": case["scenario"], "actual": actual, "error": None}
        except Exception as exc:
            if attempt == retry:
                return {"id": case["id"], "scenario": case["scenario"], "actual": {}, "error": str(exc)}
            time.sleep(2 ** attempt)
    return {}  # unreachable


def print_report(results: list[dict], agg: dict) -> None:
    print("\n" + "=" * 70)
    print("ClearNote Summarization Eval — Per-Case Results")
    print("=" * 70)

    for r in results:
        s = r["scores"]
        urgency_mark = "✓" if s["urgency_correct"] else "✗"
        print(
            f"\n[{r['id']}] {r['scenario']}"
        )
        if r.get("error"):
            print(f"  ERROR: {r['error']}")
            continue
        print(f"  Urgency  : {urgency_mark} expected={s['urgency_expected']}  got={s['urgency_actual']}")
        print(f"  Meds     : recall={s['medications']['recall']:.0%}  precision={s['medications']['precision']:.0%}  f1={s['medications']['f1']:.0%}")
        print(f"  Diagnoses: recall={s['diagnoses']['recall']:.0%}  precision={s['diagnoses']['precision']:.0%}  f1={s['diagnoses']['f1']:.0%}")
        print(f"  Actions  : recall={s['action_items']['recall']:.0%}  precision={s['action_items']['precision']:.0%}  f1={s['action_items']['f1']:.0%}")
        print(f"  Composite: {s['composite_score']:.1%}")

    print("\n" + "=" * 70)
    print("Aggregate Results")
    print("=" * 70)
    print(f"  Cases evaluated     : {agg['n']}")
    print(f"  Urgency accuracy    : {agg['urgency_accuracy']:.1%}")
    print(f"  Medication recall   : {agg['medication_recall']:.1%}  (f1: {agg['medication_f1']:.1%})")
    print(f"  Diagnosis recall    : {agg['diagnosis_recall']:.1%}  (f1: {agg['diagnosis_f1']:.1%})")
    print(f"  Action item recall  : {agg['action_item_recall']:.1%}  (f1: {agg['action_item_f1']:.1%})")
    print(f"  Composite score     : {agg['composite_score']:.1%}")
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="Run a single case by id")
    parser.add_argument("--out", help="Write JSON results to this file")
    args = parser.parse_args()

    cases = load_cases(filter_id=args.case)
    if not cases:
        print(f"No cases found{' for id=' + args.case if args.case else ''}.")
        sys.exit(1)

    ai = AIService()

    from eval.metrics import score_case, aggregate  # noqa: E402

    results = []
    for i, case in enumerate(cases, 1):
        print(f"Running {case['id']} ({i}/{len(cases)}) — {case['scenario']} ...", end=" ", flush=True)
        raw = run_case(ai, case)
        scores = score_case(case["expected"], raw["actual"]) if not raw.get("error") else {}
        results.append({**raw, "expected": case["expected"], "scores": scores})
        status = f"composite={scores.get('composite_score', 0):.0%}" if not raw.get("error") else f"ERROR: {raw['error']}"
        print(status)

    valid = [r for r in results if not r.get("error")]
    agg = aggregate([r["scores"] for r in valid])

    print_report(results, agg)

    if args.out:
        out_path = Path(args.out)
        with open(out_path, "w") as f:
            json.dump({"aggregate": agg, "cases": results}, f, indent=2)
        print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()
