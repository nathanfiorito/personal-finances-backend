import sys
from pathlib import Path

from importlinter.cli import lint_imports


def test_hexagonal_contracts():
    """Enforce hexagonal architecture boundaries via import-linter.

    Runs `lint_imports` against the .importlinter config at the project root.
    Fails with a readable diff if any declared contract is violated.
    """
    project_root = Path(__file__).parent.parent.parent  # personal-finances-backend/

    # Save current cwd and change to project root for import-linter
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(str(project_root))

        # Capture exit status from lint_imports
        exit_status = lint_imports(
            config_filename=".importlinter",
            verbose=False,
        )

        assert exit_status == 0, (
            f"Architecture contract violations detected. Exit status: {exit_status}\n"
            "Run `python -m importlinter` locally for detailed output."
        )
    finally:
        import os
        os.chdir(str(original_cwd))
