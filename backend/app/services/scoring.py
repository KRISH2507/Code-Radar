"""
Health Score Calculator

Score = 100 minus weighted, capped penalties per severity.
The caps prevent a single noisy rule from dominating.
"""

from typing import Dict


# Penalty per issue occurrence and cap (max deduction) per severity level
_PENALTIES: Dict[str, Dict[str, float]] = {
    "critical": {"per": 10.0, "cap": 40.0},
    "high":     {"per":  5.0, "cap": 30.0},
    "medium":   {"per":  2.0, "cap": 20.0},
    "low":      {"per":  0.5, "cap":  5.0},
    "info":     {"per":  0.1, "cap":  2.0},
}


def calculate_health_score(
    critical: int,
    high: int,
    medium: int,
    low: int,
    info: int,
) -> float:
    """
    Return a health score between 0 and 100 (two decimal places).

    Parameters map directly to the issue count per severity returned by the
    analyser.  Score is deterministic and cheap to recalculate.
    """
    counts = {
        "critical": critical,
        "high":     high,
        "medium":   medium,
        "low":      low,
        "info":     info,
    }

    total_deduction = 0.0
    for severity, count in counts.items():
        p = _PENALTIES[severity]
        deduction = min(count * p["per"], p["cap"])
        total_deduction += deduction

    score = max(0.0, round(100.0 - total_deduction, 2))
    return score


def score_from_issue_list(issues) -> float:
    """
    Convenience wrapper – accepts a list of objects / dicts that have a
    ``severity`` attribute/key.
    """
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for issue in issues:
        sev = issue.severity if hasattr(issue, "severity") else issue.get("severity", "info")
        if sev in counts:
            counts[sev] += 1
    return calculate_health_score(**counts)
