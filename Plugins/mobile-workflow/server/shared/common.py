"""Shared types and helpers for all validators."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass
class Issue:
    severity: Literal["error", "warning", "info"]
    message: str
    element_id: str | None = None
    rule: str | None = None
    line: int | None = None


def result(issues: list[Issue]) -> dict:
    errors   = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity in ("warning", "info")]
    return {
        "error_count":   len(errors),
        "warning_count": len(warnings),
        "errors":   [fmt(i) for i in errors],
        "warnings": [fmt(i) for i in warnings],
    }


def fmt(i: Issue) -> dict:
    d: dict = {"message": i.message}
    if i.element_id is not None: d["element_id"] = i.element_id
    if i.rule       is not None: d["rule"]       = i.rule
    if i.line       is not None: d["line"]       = i.line
    return d
