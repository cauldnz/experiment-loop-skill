"""Blocking Evidence Gate for experiment-loop runs."""

from ._gate import validate_experiment
from ._model import CheckResult, EvidenceReport

__all__ = ["CheckResult", "EvidenceReport", "validate_experiment"]
