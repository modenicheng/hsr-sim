from __future__ import annotations

from rich.text import Text
from rich.style import Style
from textual.widget import Widget

_FLASH_DELAY = 0.2
_DECAY_INTERVAL = 0.04
_DECAY_STEPS = 5


class HpBarWidget(Widget):
    """Two-layer HP bar with damage/heal animation.

    Upper layer: HP bar (colored + optional flash portion).
    Lower layer: shield bar (white).

    Animation phases:
      flash (0.2s) -> decay (5 ticks over 0.2s) -> idle
    Damage: lost portion turns white, then decays.
    Heal:   gained portion turns green, then decays.
    """

    DEFAULT_CSS = """
    HpBarWidget {
        height: 2;
        width: 100%;
    }
    """

    def __init__(
        self,
        value: float = 0.0,
        max_value: float = 100.0,
        shield: float = 0.0,
        color: str = "cyan",
        show_percent: bool = True,
        bar_width: int = 0,
        prefix: str = "",
        shield_indent: int = 0,
        name: str = "",
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.value = value
        self.max_value = max_value
        self.shield = shield
        self.color = color
        self.show_percent = show_percent
        self.bar_width = bar_width
        self.prefix = prefix
        self.shield_indent = shield_indent

        # ── Animation state ──
        self._anim_state: str = "idle"  # idle | flash | decay
        self._flash_type: str = "damage"  # damage | heal
        self._total_flash: int = 0
        self._target_fill: int = 0
        self._decay_step: int = 0
        self._anim_bar_w: int = 0
        self._delay_timer: object = None
        self._decay_timer: object = None

    def update_hp(
        self,
        value: float,
        max_value: float | None = None,
        shield: float | None = None,
    ) -> None:
        """Update HP value; triggers animation if HP changed."""
        if max_value is not None:
            self.max_value = max_value
        if shield is not None:
            self.shield = shield

        old = self.value
        self.value = value

        if value != old:
            self._start_animation(old, value)
        else:
            self.refresh()

    # ── Animation ──────────────────────────────────

    def _start_animation(self, old_val: float, new_val: float) -> None:
        self._stop_timers()

        max_val = max(self.max_value, 1.0)
        bar_w = self._bar_width()
        self._anim_bar_w = bar_w

        old_fill = int(bar_w * max(0.0, old_val) / max_val)
        new_fill = int(bar_w * max(0.0, new_val) / max_val)

        delta = abs(new_fill - old_fill)
        if delta <= 0:
            self._anim_state = "idle"
            self.refresh()
            return

        self._target_fill = new_fill
        self._total_flash = delta
        self._decay_step = 0

        if new_val < old_val:
            self._flash_type = "damage"
        else:
            self._flash_type = "heal"

        self._anim_state = "flash"
        self.refresh()
        self._delay_timer = self.set_timer(
            _FLASH_DELAY, self._on_delay_done
        )

    def _on_delay_done(self) -> None:
        self._anim_state = "decay"
        self._decay_timer = self.set_interval(
            _DECAY_INTERVAL, self._on_decay_tick
        )

    def _on_decay_tick(self) -> None:
        self._decay_step += 1
        self.refresh()
        if self._decay_step >= _DECAY_STEPS:
            self._anim_state = "idle"
            if self._decay_timer:
                self._decay_timer.stop()
                self._decay_timer = None

    def _stop_timers(self) -> None:
        if self._delay_timer is not None:
            self._delay_timer.stop()
            self._delay_timer = None
        if self._decay_timer is not None:
            self._decay_timer.stop()
            self._decay_timer = None

    # ── Render ─────────────────────────────────────

    def render(self) -> Text:
        max_val = max(self.max_value, 1.0)
        safe_val = max(0.0, self.value)
        safe_shield = max(0.0, self.shield)

        total_w = self.size.width
        if total_w <= 0:
            total_w = self.bar_width if self.bar_width > 0 else 20

        pct_text = ""
        if self.show_percent:
            pct = safe_val / max_val * 100
            pct_text = f"[{pct:.0f}%]"
        pct_suffix = f" {pct_text}" if pct_text else ""

        max_w = total_w - len(self.prefix) - len(pct_suffix)
        max_w = max(1, max_w)

        hp_fill = min(int(max_w * safe_val / max_val), max_w)
        bar_w = self._anim_bar_w if self._anim_state != "idle" else max_w

        # Shield line (always rendered)
        sw = min(int(max_w * safe_shield / max_val), max_w)
        shield_line = Text()
        if self.shield_indent > 0:
            shield_line.append(" " * self.shield_indent)
        shield_line.append("=" * sw, style=Style(color="white"))

        # HP line
        hp_line = self._render_hp_line(hp_fill, bar_w, max_w)

        result = Text()
        result.append(hp_line)
        if pct_suffix:
            result.append(pct_suffix, style=Style(color="white"))
        result.append("\n")
        result.append(shield_line)
        return result

    def _render_hp_line(
        self, hp_fill: int, bar_w: int, real_w: int
    ) -> Text:
        """Render the HP bar portion with optional animation overlay."""
        line = Text()
        if self.prefix:
            line.append(self.prefix, style=Style(color="white"))

        if self._anim_state == "idle":
            colored = hp_fill
            empty = real_w - colored
            line.append("=" * colored, style=Style(color=self.color))
            line.append("-" * max(0, empty), style=Style(color="grey42"))
            return line

        # Animation active — use saved bar_w for consistent flash scaling
        progress = (
            min(1.0, self._decay_step / _DECAY_STEPS)
            if self._anim_state == "decay"
            else 0.0
        )
        flash_visible = int(self._total_flash * (1.0 - progress))

        if self._flash_type == "damage":
            colored = int(bar_w * hp_fill / real_w) if real_w > 0 else 0
            empty = real_w - colored - flash_visible
            line.append("=" * max(0, colored), style=Style(color=self.color))
            line.append("=" * max(0, flash_visible), style=Style(color="white"))
            line.append("-" * max(0, empty), style=Style(color="grey42"))
        else:  # heal
            # Base = old fill; filled = portion already transitioned
            base = hp_fill - self._total_flash
            filled = int(self._total_flash * progress)
            colored = max(0, base) + filled
            empty = real_w - colored - flash_visible
            line.append("=" * max(0, colored), style=Style(color=self.color))
            line.append(
                "=" * max(0, flash_visible), style=Style(color="green")
            )
            line.append("-" * max(0, empty), style=Style(color="grey42"))

        return line

    def _bar_width(self) -> int:
        total_w = self.size.width
        if total_w <= 0:
            total_w = self.bar_width if self.bar_width > 0 else 20
        pct_text = ""
        if self.show_percent:
            pct = max(0.0, self.value) / max(self.max_value, 1.0) * 100
            pct_text = f"[{pct:.0f}%]"
        pct_suffix = f" {pct_text}" if pct_text else ""
        return max(1, total_w - len(self.prefix) - len(pct_suffix))
