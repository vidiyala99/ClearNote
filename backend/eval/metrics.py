"""
Metric functions for SOAP note extraction evaluation.

All list-based fields (medications, diagnoses, action_items) use substring-based
recall and precision to handle paraphrase and partial matches (e.g. "ibuprofen 400mg"
matches "ibuprofen 400mg every six hours as needed").
"""
from __future__ import annotations

import re


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _matched(query: str, candidates: list[str]) -> bool:
    """True if any candidate contains query as a substring, or vice versa."""
    q = _normalize(query)
    for c in candidates:
        cn = _normalize(c)
        if q in cn or cn in q:
            return True
    return False


def list_recall(expected: list[str], actual: list[str]) -> float:
    """Fraction of expected items found in actual output."""
    if not expected:
        return 1.0
    return sum(1 for e in expected if _matched(e, actual)) / len(expected)


def list_precision(expected: list[str], actual: list[str]) -> float:
    """Fraction of actual items that correspond to something expected."""
    if not actual:
        return 1.0
    return sum(1 for a in actual if _matched(a, expected)) / len(actual)


def list_f1(expected: list[str], actual: list[str]) -> dict:
    r = list_recall(expected, actual)
    p = list_precision(expected, actual)
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}


def urgency_accuracy(expected: str, actual: str) -> bool:
    return _normalize(expected) == _normalize(actual)


def score_case(expected: dict, actual: dict) -> dict:
    """Return per-field scores for a single case."""
    urgency_hit = urgency_accuracy(expected["urgency_tag"], actual.get("urgency_tag", ""))
    med_scores = list_f1(expected["medications"], actual.get("medications", []))
    diag_scores = list_f1(expected["diagnoses"], actual.get("diagnoses", []))
    action_scores = list_f1(expected["action_items"], actual.get("action_items", []))

    composite = (
        (1.0 if urgency_hit else 0.0)
        + med_scores["recall"]
        + diag_scores["recall"]
        + action_scores["recall"]
    ) / 4.0

    return {
        "urgency_correct": urgency_hit,
        "urgency_expected": expected["urgency_tag"],
        "urgency_actual": actual.get("urgency_tag", ""),
        "medications": med_scores,
        "diagnoses": diag_scores,
        "action_items": action_scores,
        "composite_score": round(composite, 3),
    }


def aggregate(scores: list[dict]) -> dict:
    n = len(scores)
    if not n:
        return {}

    def avg(key, sub=None):
        if sub:
            return round(sum(s[key][sub] for s in scores) / n, 3)
        return round(sum(s[key] for s in scores) / n, 3)

    urgency_acc = round(sum(1 for s in scores if s["urgency_correct"]) / n, 3)

    return {
        "n": n,
        "urgency_accuracy": urgency_acc,
        "medication_recall": avg("medications", "recall"),
        "medication_precision": avg("medications", "precision"),
        "medication_f1": avg("medications", "f1"),
        "diagnosis_recall": avg("diagnoses", "recall"),
        "diagnosis_precision": avg("diagnoses", "precision"),
        "diagnosis_f1": avg("diagnoses", "f1"),
        "action_item_recall": avg("action_items", "recall"),
        "action_item_precision": avg("action_items", "precision"),
        "action_item_f1": avg("action_items", "f1"),
        "composite_score": avg("composite_score"),
    }
