from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import load_jd_config


@dataclass(frozen=True)
class JobDefinition:
    raw: dict[str, Any]

    @property
    def job(self) -> dict[str, Any]:
        return self.raw["job"]

    @property
    def skill_groups(self) -> dict[str, list[str]]:
        return self.raw["skill_groups"]

    @property
    def signals(self) -> dict[str, list[str]]:
        return self.raw["signals"]

    @property
    def company_rules(self) -> dict[str, list[str]]:
        return self.raw["company_rules"]

    @property
    def title_rules(self) -> dict[str, list[str]]:
        return self.raw["title_rules"]

    @property
    def retrieval_text(self) -> str:
        terms = [term for values in self.skill_groups.values() for term in values]
        return " ".join([self.job["title"], self.job["summary"], *terms, *self.signals["production"], *self.signals["shipper"]])


def load_job() -> JobDefinition:
    return JobDefinition(load_jd_config())
