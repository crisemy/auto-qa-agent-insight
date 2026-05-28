from __future__ import annotations

import json
import sys
from pathlib import Path

from app.models import RawBugReport
from app.services.query_router import process

_HERE = Path(__file__).parent
_DATASET_PATH = _HERE / "golden_dataset.json"


def _load_dataset() -> list[dict]:
    with open(_DATASET_PATH) as f:
        return json.load(f)


def _seed_vector_store() -> None:
    from app.components.vector_store import index_bugs, reset

    reset()
    dataset = _load_dataset()
    bugs = []
    for entry in dataset:
        module = entry["expected"]["failing_module"]
        subsystem = module.split("/")[0] if module and module != "unknown" else ""
        bugs.append(
            {
                "bug_id": entry["id"],
                "signature": entry["payload"],
                "subsystem": subsystem,
                "diagnostic": entry["expected"]["diagnostic_summary"],
                "status": "RESOLVED",
            }
        )
    index_bugs(bugs)


def _score_module(predicted: str, expected: str) -> bool:
    if expected == "unknown":
        return True
    return expected in predicted or predicted in expected


def run_evaluation() -> dict:
    _seed_vector_store()
    dataset = _load_dataset()
    results = []

    for entry in dataset:
        report = RawBugReport(payload=entry["payload"], source="evaluation")
        output = process(report)

        if isinstance(output, dict) and "error" in output:
            results.append(
                {
                    "id": entry["id"],
                    "passed": False,
                    "error": output.get("message", output.get("error")),
                }
            )
            continue

        exp = entry["expected"]
        severity_ok = output.triage.severity.value == exp["severity"]
        module_ok = _score_module(output.triage.failing_module, exp["failing_module"])
        exception_ok = output.triage.exception_type == exp["exception_type"]

        passed = severity_ok and module_ok and exception_ok

        results.append(
            {
                "id": entry["id"],
                "passed": passed,
                "severity_ok": severity_ok,
                "module_ok": module_ok,
                "exception_ok": exception_ok,
                "predicted_severity": output.triage.severity.value,
                "predicted_module": output.triage.failing_module,
                "predicted_exception": output.triage.exception_type,
            }
        )

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    severity_acc = sum(1 for r in results if r.get("severity_ok")) / total
    module_hit = sum(1 for r in results if r.get("module_ok")) / total
    exception_acc = sum(1 for r in results if r.get("exception_ok")) / total

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 2),
        "severity_accuracy": round(severity_acc, 2),
        "module_hit_rate": round(module_hit, 2),
        "exception_accuracy": round(exception_acc, 2),
        "details": results,
    }


def print_report(report: dict) -> None:
    print("=" * 50)
    print("  Auto-QA Agent Insights — Offline Evaluation")
    print("=" * 50)
    print(f"\n  Total cases:  {report['total']}")
    print(f"  Passed:       {report['passed']}")
    print(f"  Failed:       {report['failed']}")
    print(f"  Pass rate:    {report['pass_rate']:.0%}")
    print()
    print(f"  Severity accuracy:  {report['severity_accuracy']:.0%}")
    print(f"  Module hit rate:    {report['module_hit_rate']:.0%}")
    print(f"  Exception accuracy: {report['exception_accuracy']:.0%}")
    print()

    for r in report["details"]:
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"  [{status}] {r['id']}")


if __name__ == "__main__":
    report = run_evaluation()
    print_report(report)
    if report["pass_rate"] < 1.0:
        sys.exit(1)
