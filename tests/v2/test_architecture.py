import subprocess
import sys
from pathlib import Path


def test_hexagonal_contracts():
    """Enforce hexagonal architecture boundaries via import-linter.

    Runs lint_imports_command via subprocess against the .importlinter config
    at the project root. Fails with a readable diff if any contract is violated.
    """
    project_root = Path(__file__).parent.parent.parent  # personal-finances-backend/
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports_command; lint_imports_command()",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    assert result.returncode == 0, (
        "Architecture contract violations detected:\n"
        + result.stdout
        + result.stderr
    )
