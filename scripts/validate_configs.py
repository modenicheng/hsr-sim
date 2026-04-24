"""Validate all config files in the configs directory.

Checks:
- JSON format validity
- ID uniqueness across all configs
- Python script compliance (inherits BaseSkill, has execute method)
"""

from argparse import ArgumentParser, Namespace
import ast
import json
from pathlib import Path
import re
from typing import Any
import os

from hsr_sim.core.config import CONFIGS_DIR
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# Issue categories
ISSUE_ERROR = "error"
ISSUE_WARNING = "warning"
ISSUE_INFO = "info"


class ConfigValidator:
    """Validate all config files."""

    def __init__(self):
        self.issues: list[dict[str, Any]] = []
        self.id_registry: dict[int, list[str]] = {}  # id -> list of paths
        self.processed_files: int = 0
        self.versions: list[str] = []

    def validate_all(self, version: str | None = None) -> None:
        """Scan and validate all configs in specified version or all versions."""
        self._scan_versions(version)
        if not self.versions:
            console.print("[yellow]No valid version directories found[/yellow]")
            return

        for ver in self.versions:
            self._validate_version(ver)

    def _scan_versions(self, version: str | None) -> None:
        """Identify all config versions."""
        if version:
            normalized = self._normalize_version(version)
            if (CONFIGS_DIR / normalized).exists():
                self.versions = [normalized]
            return

        pattern = re.compile(r"^v(\d+)\.(\d+)$")
        versions = [
            p.name
            for p in CONFIGS_DIR.iterdir()
            if p.is_dir() and pattern.match(p.name)
        ]
        self.versions = sorted(versions)

    def _validate_version(self, version: str) -> None:
        """Validate all configs in a specific version."""
        version_root = CONFIGS_DIR / version

        # Validate characters, light_cones, relics, buffs, enemies
        self._validate_characters(version, version_root / "characters")
        self._validate_light_cones(version, version_root / "light_cones")
        self._validate_relics(version, version_root / "relics")
        self._validate_buffs(version, version_root / "buffs")
        self._validate_enemies(version, version_root / "enemies")

    def _validate_characters(self, version: str, chars_root: Path) -> None:
        """Validate character configs and scripts."""
        if not chars_root.exists():
            return

        for char_dir in chars_root.iterdir():
            if not char_dir.is_dir():
                continue

            char_name = char_dir.name
            json_file = char_dir / f"{char_name}.json"

            if json_file.exists():
                self._validate_json(version, "character", json_file)

            # Validate character-related scripts
            for script_type in [
                "skills",
                "talent",
                "technique",
                "eidolons",
                "bonus_ability",
            ]:
                script_dir = char_dir / script_type
                if script_dir.exists():
                    for py_file in script_dir.glob("*.py"):
                        self._validate_python_script(
                            version, "character", py_file
                        )

            # Validate character-scoped buffs
            buffs_root = char_dir / "buffs"
            if buffs_root.exists():
                for buff_dir in buffs_root.iterdir():
                    if buff_dir.is_dir():
                        buff_json = buff_dir / f"{buff_dir.name}.json"
                        if buff_json.exists():
                            self._validate_json(version, "buff", buff_json)
                        for py_file in buff_dir.glob("*.py"):
                            self._validate_python_script(
                                version, "buff", py_file
                            )

    def _validate_light_cones(self, version: str, lc_root: Path) -> None:
        """Validate light cone configs and scripts."""
        if not lc_root.exists():
            return

        for lc_dir in lc_root.iterdir():
            if not lc_dir.is_dir():
                continue

            lc_name = lc_dir.name
            json_file = lc_dir / f"{lc_name}.json"

            if json_file.exists():
                self._validate_json(version, "light_cone", json_file)

            for py_file in lc_dir.glob("*.py"):
                self._validate_python_script(version, "light_cone", py_file)

    def _validate_relics(self, version: str, relics_root: Path) -> None:
        """Validate relic set configs and scripts."""
        if not relics_root.exists():
            return

        for set_dir in relics_root.iterdir():
            if not set_dir.is_dir():
                continue

            set_name = set_dir.name

            for json_file in set_dir.glob("*.json"):
                self._validate_json(version, "relic", json_file)

            for py_file in set_dir.glob("*.py"):
                self._validate_python_script(version, "relic", py_file)

    def _validate_buffs(self, version: str, buffs_root: Path) -> None:
        """Validate global buff configs and scripts."""
        if not buffs_root.exists():
            return

        for buff_dir in buffs_root.iterdir():
            if not buff_dir.is_dir():
                continue

            buff_json = buff_dir / f"{buff_dir.name}.json"
            if buff_json.exists():
                self._validate_json(version, "buff", buff_json)

            for py_file in buff_dir.glob("*.py"):
                self._validate_python_script(version, "buff", py_file)

    def _validate_enemies(self, version: str, enemies_root: Path) -> None:
        """Validate enemy configs and scripts."""
        if not enemies_root.exists():
            return

        for enemy_dir in enemies_root.iterdir():
            if not enemy_dir.is_dir():
                continue

            enemy_name = enemy_dir.name
            json_file = enemy_dir / f"{enemy_name}.json"

            if json_file.exists():
                self._validate_json(version, "enemy", json_file)

            for script_type in ["skills", "passives"]:
                script_dir = enemy_dir / script_type
                if script_dir.exists():
                    for py_file in script_dir.glob("*.py"):
                        self._validate_python_script(version, "enemy", py_file)

    def _validate_json(
        self, version: str, config_type: str, json_path: Path
    ) -> None:
        """Validate JSON format and check for ID duplicates."""
        self.processed_files += 1
        try:
            rel_path = json_path.relative_to(CONFIGS_DIR)
        except ValueError:
            # Handle paths outside CONFIGS_DIR (e.g., in tests)
            rel_path = Path(os.path.relpath(json_path, CONFIGS_DIR.parent))

        try:
            with json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Check for id field
            if "id" in data:
                entity_id = data["id"]
                if isinstance(entity_id, int):
                    if entity_id not in self.id_registry:
                        self.id_registry[entity_id] = []
                    self.id_registry[entity_id].append(str(rel_path))

        except json.JSONDecodeError as exc:
            self._add_issue(
                ISSUE_ERROR,
                config_type,
                str(rel_path),
                f"JSON decode error: {exc.msg} at line {exc.lineno}",
            )
        except Exception as exc:
            self._add_issue(
                ISSUE_ERROR,
                config_type,
                str(rel_path),
                f"Unexpected error: {exc}",
            )

    def _validate_python_script(
        self, version: str, config_type: str, py_path: Path
    ) -> None:
        """Validate Python script format and compliance."""
        self.processed_files += 1
        try:
            rel_path = py_path.relative_to(CONFIGS_DIR)
        except ValueError:
            # Handle paths outside CONFIGS_DIR (e.g., in tests)
            rel_path = Path(os.path.relpath(py_path, CONFIGS_DIR.parent))

        try:
            content = py_path.read_text(encoding="utf-8")
            ast.parse(content)

            # Check if it imports BaseSkill
            if (
                "from hsr_sim.skills.script_loader import BaseSkill"
                not in content
            ):
                self._add_issue(
                    ISSUE_WARNING,
                    config_type,
                    str(rel_path),
                    "Does not import BaseSkill",
                )

            # Check if it defines a class
            tree = ast.parse(content)
            has_class = any(
                isinstance(node, ast.ClassDef) for node in ast.walk(tree)
            )
            if not has_class:
                self._add_issue(
                    ISSUE_ERROR,
                    config_type,
                    str(rel_path),
                    "No class definition found",
                )
                return

            # Check if class has execute method
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    has_execute = any(
                        isinstance(n, ast.FunctionDef) and n.name == "execute"
                        for n in node.body
                    )
                    if not has_execute:
                        self._add_issue(
                            ISSUE_WARNING,
                            config_type,
                            str(rel_path),
                            "Class does not have execute method",
                        )

        except SyntaxError as exc:
            self._add_issue(
                ISSUE_ERROR,
                config_type,
                str(rel_path),
                f"Syntax error: {exc.msg} at line {exc.lineno}",
            )
        except Exception as exc:
            self._add_issue(
                ISSUE_ERROR,
                config_type,
                str(rel_path),
                f"Unexpected error: {exc}",
            )

    def _add_issue(
        self, level: str, config_type: str, path: str, message: str
    ) -> None:
        """Record an issue."""
        self.issues.append(
            {
                "level": level,
                "type": config_type,
                "path": path,
                "message": message,
            }
        )

    def _check_duplicate_ids(self) -> None:
        """Check for duplicate IDs across all configs."""
        for entity_id, paths in self.id_registry.items():
            if len(paths) > 1:
                self._add_issue(
                    ISSUE_ERROR,
                    "id_duplicate",
                    f"ID {entity_id}",
                    f"Found in: {', '.join(paths)}",
                )

    @staticmethod
    def _normalize_version(version: str) -> str:
        """Normalize version string to vX.X format."""
        matched = re.fullmatch(r"v?(\d+\.\d+)", version)
        if not matched:
            raise ValueError("version format only supports x.x or vx.x")
        return f"v{matched.group(1)}"

    def report(self) -> None:
        """Print validation report."""
        self._check_duplicate_ids()

        # Group issues by level
        errors = [i for i in self.issues if i["level"] == ISSUE_ERROR]
        warnings = [i for i in self.issues if i["level"] == ISSUE_WARNING]

        # Summary panel
        summary_text = (
            f"[cyan]Versions: {len(self.versions)}[/cyan]\n"
            f"[cyan]Files processed: {self.processed_files}[/cyan]\n"
            f"[red]Errors: {len(errors)}[/red]\n"
            f"[yellow]Warnings: {len(warnings)}[/yellow]"
        )

        console.print(
            Panel(
                summary_text,
                title="[bold]Validation Summary[/bold]",
                border_style="blue",
            )
        )

        # Errors table
        if errors:
            error_table = Table(
                title="[red][bold]Errors[/bold][/red]",
                show_header=True,
                header_style="bold red",
            )
            error_table.add_column("Type", style="cyan")
            error_table.add_column("Path", style="magenta")
            error_table.add_column("Message", style="red")

            for issue in errors:
                error_table.add_row(
                    issue["type"],
                    issue["path"],
                    issue["message"],
                )

            console.print(error_table)

        # Warnings table
        if warnings:
            warning_table = Table(
                title="[yellow][bold]Warnings[/bold][/yellow]",
                show_header=True,
                header_style="bold yellow",
            )
            warning_table.add_column("Type", style="cyan")
            warning_table.add_column("Path", style="magenta")
            warning_table.add_column("Message", style="yellow")

            for issue in warnings:
                warning_table.add_row(
                    issue["type"],
                    issue["path"],
                    issue["message"],
                )

            console.print(warning_table)

        # Overall status
        if errors:
            status = Text("❌ Validation failed", style="bold red")
        elif warnings:
            status = Text(
                "⚠️  Validation passed with warnings", style="bold yellow"
            )
        else:
            status = Text("✅ All validations passed", style="bold green")

        console.print(Panel(status, border_style="blue"))


def parse_args() -> Namespace:
    """Parse CLI arguments."""
    parser = ArgumentParser(description="Validate all config files")
    parser.add_argument(
        "--version",
        "-v",
        default=None,
        help="Validate specific version (e.g., v1.0 or 1.0). If not specified, validates all versions.",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    validator = ConfigValidator()
    validator.validate_all(args.version)
    validator.report()


if __name__ == "__main__":
    main()
