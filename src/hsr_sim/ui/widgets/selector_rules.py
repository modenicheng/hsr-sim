from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TargetInfo:
    """Describes a selectable target for the selector widget."""

    entity_id: int
    label: str
    is_enemy: bool
    is_alive: bool = True


@dataclass
class SelectionMark:
    """A selected target marker description.

    is_primary controls whether marker should use solid arrow.
    """

    entity_id: int
    is_primary: bool = False


class SelectorRule(Protocol):
    """Protocol for custom selector rules.

    Implementations return a list of (entity_id, is_primary) tuples.
    is_primary=True means solid arrow (▲), False means hollow (△).
    """

    def select_targets(
        self, targets: list[TargetInfo], primary: int | None
    ) -> list[SelectionMark]:
        """Select which targets to mark with arrows.

        Args:
            targets: All available targets
            primary: The primary target entity_id (main target cursor position)

        Returns:
            List of selected target marks
        """
        ...


@dataclass
class SingleTargetRule:
    """Single-target selector: one solid arrow on the primary target."""

    def select_targets(
        self, targets: list[TargetInfo], primary: int | None
    ) -> list[SelectionMark]:
        if primary is None:
            return []
        for t in targets:
            if t.entity_id == primary:
                return [SelectionMark(entity_id=t.entity_id, is_primary=True)]
        return []


@dataclass
class BlastRule:
    """Blast spread selector: solid on primary, hollow on adjacent."""

    def select_targets(
        self, targets: list[TargetInfo], primary: int | None
    ) -> list[SelectionMark]:
        if primary is None:
            return []
        primary_idx = None
        for i, t in enumerate(targets):
            if t.entity_id == primary:
                primary_idx = i
                break
        if primary_idx is None:
            return []
        result: list[SelectionMark] = []
        for i, t in enumerate(targets):
            if i == primary_idx:
                result.append(
                    SelectionMark(entity_id=t.entity_id, is_primary=True)
                )
            elif abs(i - primary_idx) == 1:
                result.append(
                    SelectionMark(entity_id=t.entity_id, is_primary=False)
                )
        return result


@dataclass
class AoERule:
    """AoE selector: hollow arrows on all targets."""

    def select_targets(
        self, targets: list[TargetInfo], primary: int | None
    ) -> list[SelectionMark]:
        return [
            SelectionMark(entity_id=t.entity_id, is_primary=False)
            for t in targets
        ]
