"""Test suite for config validation script."""

from pathlib import Path

from scripts.validate_configs import ConfigValidator


def test_validator_detects_json_errors(tmp_path):
    """Test that validator detects JSON format errors."""
    # Create a temp config structure
    version_dir = tmp_path / "configs" / "v1.0"
    enemies_dir = version_dir / "enemies" / "test_enemy"
    enemies_dir.mkdir(parents=True, exist_ok=True)

    # Create a valid JSON first
    valid_json = enemies_dir / "test_enemy.json"
    valid_json.write_text('{"id": 12345, "name": "test"}')

    # Create an invalid JSON
    invalid_json = enemies_dir / "invalid.json"
    invalid_json.write_text('{"id": 12346, "invalid json}')

    # Validate
    validator = ConfigValidator()
    validator._validate_json("v1.0", "enemy", valid_json)
    validator._validate_json("v1.0", "enemy", invalid_json)

    # Check for errors
    errors = [i for i in validator.issues if i["level"] == "error"]
    assert len(errors) >= 1, "Should detect JSON decode error"
    assert "JSON decode error" in errors[0]["message"]


def test_validator_detects_duplicate_ids(tmp_path):
    """Test that validator detects duplicate IDs."""
    version_dir = tmp_path / "configs" / "v1.0"
    enemies_dir = version_dir / "enemies" / "test_enemy"
    enemies_dir.mkdir(parents=True, exist_ok=True)

    # Create two JSON files with the same ID
    json1 = enemies_dir / "enemy1.json"
    json1.write_text('{"id": 99999, "name": "enemy1"}')

    json2 = enemies_dir / "enemy2.json"
    json2.write_text('{"id": 99999, "name": "enemy2"}')

    # Validate
    validator = ConfigValidator()
    validator._validate_json("v1.0", "enemy", json1)
    validator._validate_json("v1.0", "enemy", json2)
    validator._check_duplicate_ids()

    # Check for duplicate ID error
    errors = [i for i in validator.issues if i["level"] == "error"]
    dup_errors = [e for e in errors if "duplicate" in e["type"] or "Found in" in e["message"]]
    assert len(dup_errors) >= 1, "Should detect duplicate IDs"


def test_validator_detects_python_syntax_errors(tmp_path):
    """Test that validator detects Python syntax errors."""
    version_dir = tmp_path / "configs" / "v1.0"
    enemies_dir = version_dir / "enemies" / "test_enemy" / "skills"
    enemies_dir.mkdir(parents=True, exist_ok=True)

    # Create a Python file with syntax error
    bad_py = enemies_dir / "test_skill.py"
    bad_py.write_text("class TestSkill:\n    def execute(x\n        pass")

    # Validate
    validator = ConfigValidator()
    validator._validate_python_script("v1.0", "enemy", bad_py)

    # Check for syntax error
    errors = [i for i in validator.issues if i["level"] == "error"]
    sys_errors = [e for e in errors if "Syntax error" in e["message"]]
    assert len(sys_errors) >= 1, "Should detect syntax errors"


def test_validator_validates_execute_method(tmp_path):
    """Test that validator checks for execute method."""
    version_dir = tmp_path / "configs" / "v1.0"
    enemies_dir = version_dir / "enemies" / "test_enemy" / "skills"
    enemies_dir.mkdir(parents=True, exist_ok=True)

    # Create a valid Python file but without execute method
    no_execute_py = enemies_dir / "no_execute.py"
    no_execute_py.write_text(
        "from hsr_sim.skills.script_loader import BaseSkill\n\n"
        "class TestSkill(BaseSkill):\n"
        "    pass"
    )

    # Validate
    validator = ConfigValidator()
    validator._validate_python_script("v1.0", "enemy", no_execute_py)

    # Check for warning
    warnings = [i for i in validator.issues if i["level"] == "warning"]
    execute_warnings = [w for w in warnings if "execute method" in w["message"]]
    assert len(execute_warnings) >= 1, "Should warn about missing execute method"


def test_validator_checks_base_skill_import(tmp_path):
    """Test that validator checks for BaseSkill import."""
    version_dir = tmp_path / "configs" / "v1.0"
    enemies_dir = version_dir / "enemies" / "test_enemy" / "skills"
    enemies_dir.mkdir(parents=True, exist_ok=True)

    # Create a Python file without BaseSkill import
    no_import_py = enemies_dir / "no_import.py"
    no_import_py.write_text(
        "class TestSkill:\n"
        "    def execute(self):\n"
        "        pass"
    )

    # Validate
    validator = ConfigValidator()
    validator._validate_python_script("v1.0", "enemy", no_import_py)

    # Check for warning
    warnings = [i for i in validator.issues if i["level"] == "warning"]
    import_warnings = [w for w in warnings if "BaseSkill" in w["message"]]
    assert len(import_warnings) >= 1, "Should warn about missing BaseSkill import"
