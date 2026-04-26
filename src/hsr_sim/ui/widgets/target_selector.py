from __future__ import annotations

from dataclasses import dataclass

from .selector_rules import SelectorRule, TargetInfo


@dataclass
class ArrowState:
    """Rendered arrow state for one target cell."""

    symbol: str
    color: str
    is_enemy: bool
    bold: bool = False


class TargetSelector:
    """Target selection state manager (not a Textual widget).

    Manages cursor, primary target, and rule-based multi-selection.
    Provides per-target arrow states for external grid rendering.
    """

    def __init__(
        self,
        targets: list[TargetInfo] | None = None,
        primary_id: int | None = None,
        rule: SelectorRule | None = None,
    ) -> None:
        self._targets: list[TargetInfo] = targets or []
        self._primary_id = primary_id
        self._rule: SelectorRule | None = rule
        self._selected_ids: set[int] = set()
        self._primary_marked_ids: set[int] = set()

    def update_targets(
        self,
        targets: list[TargetInfo],
        primary_id: int | None = None,
        rule: SelectorRule | None = None,
    ) -> None:
        self._targets = targets
        self._primary_id = primary_id
        if rule is not None:
            self._rule = rule
        self._recalc_selection()

    def move_cursor(self, direction: int) -> None:
        alive = [t for t in self._targets if t.is_alive]
        if not alive:
            return
        ids = [t.entity_id for t in alive]
        if self._primary_id not in ids:
            self._primary_id = ids[0]
        else:
            idx = ids.index(self._primary_id)
            new_idx = (idx + direction) % len(ids)
            self._primary_id = ids[new_idx]
        self._recalc_selection()

    @property
    def targets(self) -> list[TargetInfo]:
        return list(self._targets)

    def get_primary(self) -> int | None:
        return self._primary_id

    def get_selected_ids(self) -> list[int]:
        return list(self._selected_ids)

    def get_arrow_states(
        self,
    ) -> list[ArrowState]:
        """Return arrow state for every target (ordered)."""
        states = []
        for t in self._targets:
            is_selected = t.entity_id in self._selected_ids
            is_primary = t.entity_id in self._primary_marked_ids
            color = "red" if t.is_enemy else "cyan"

            if not t.is_alive and is_selected:
                states.append(ArrowState("X", "grey42", t.is_enemy))
            elif is_selected:
                if t.is_enemy:
                    sym = "▲" if is_primary else "△"
                else:
                    sym = "▼" if is_primary else "▽"
                states.append(
                    ArrowState(sym, color, t.is_enemy, bold=is_primary)
                )
            else:
                states.append(ArrowState("", "", t.is_enemy))
        return states

    def _recalc_selection(self) -> None:
        if self._rule is None:
            if self._primary_id is not None:
                self._selected_ids = {self._primary_id}
                self._primary_marked_ids = {self._primary_id}
            else:
                self._selected_ids = set()
                self._primary_marked_ids = set()
            return
        selected = self._rule.select_targets(self._targets, self._primary_id)
        self._selected_ids = {m.entity_id for m in selected}
        self._primary_marked_ids = {
            m.entity_id for m in selected if m.is_primary
        }
