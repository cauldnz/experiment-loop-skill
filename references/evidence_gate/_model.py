from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


CheckStatus = Literal["pass", "fail", "blocked"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    detail: dict[str, object] = field(default_factory=dict)
    required: bool = True


@dataclass(frozen=True)
class EvidenceReport:
    run_dir: str
    checks: tuple[CheckResult, ...]
    schema_version: str = "1.0"

    @property
    def passed(self) -> bool:
        return all(
            not check.required or check.status == "pass"
            for check in self.checks
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_dir": self.run_dir,
            "status": "pass" if self.passed else "fail",
            "checks": [asdict(check) for check in self.checks],
        }
