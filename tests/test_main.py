"""CLI entry-point checks that run without optional GUI dependencies."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import unittest
from unittest.mock import patch
import builtins

from main import main


class TestMainCLI(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--cli", *arguments])
        return status, stdout.getvalue(), stderr.getvalue()

    def test_sample_demo(self) -> None:
        status, stdout, stderr = self.run_cli()
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertIn("optimal", stdout)
        self.assertIn("[1, 0, 0, 1]", stdout)
        self.assertIn("39.0", stdout)

    def test_default_mode_falls_back_when_pyside6_is_missing(self) -> None:
        original_import = builtins.__import__

        def without_gui(name, *args, **kwargs):
            if name.startswith("PySide6"):
                raise ImportError("PySide6 is not installed")
            return original_import(name, *args, **kwargs)

        stdout = io.StringIO()
        with patch("builtins.__import__", side_effect=without_gui), redirect_stdout(stdout):
            status = main([])
        self.assertEqual(status, 0)
        self.assertIn("Running CLI mode", stdout.getvalue())
        self.assertIn("optimal", stdout.getvalue())

    def test_dataset_argument_selects_cli_without_importing_qt(self) -> None:
        original_import = builtins.__import__

        def reject_gui(name, *args, **kwargs):
            if name.startswith("PySide6"):
                raise AssertionError("CLI must not import GUI dependencies")
            return original_import(name, *args, **kwargs)

        dataset = Path(__file__).resolve().parents[1] / "assets/datasets/sample_01.json"
        with patch("builtins.__import__", side_effect=reject_gui), redirect_stdout(io.StringIO()):
            status = main(["--dataset", str(dataset)])
        self.assertEqual(status, 0)

    def test_load_datasets(self) -> None:
        dataset_dir = Path(__file__).resolve().parents[1] / "assets" / "datasets"
        for extension in ("json", "csv"):
            with self.subTest(extension=extension):
                status, stdout, stderr = self.run_cli(
                    "--dataset", str(dataset_dir / f"sample_01.{extension}")
                )
                self.assertEqual(status, 0, stderr)
                self.assertIn("optimal", stdout)
                self.assertIn("39.0", stdout)

    def test_generated_problem(self) -> None:
        status, stdout, stderr = self.run_cli(
            "--n-items", "8", "--capacity-ratio", "0.6", "--seed", "123"
        )
        self.assertEqual(status, 0, stderr)
        self.assertIn("synthetic", stdout)
        self.assertIn("optimal", stdout)

    def test_solver_limits_are_forwarded(self) -> None:
        status, stdout, stderr = self.run_cli("--max-expanded-nodes", "1")
        self.assertEqual(status, 0, stderr)
        self.assertIn("max_expanded", stdout)
        status, stdout, stderr = self.run_cli("--time-limit", "1e-20")
        self.assertEqual(status, 0, stderr)
        self.assertIn("time_limit", stdout)

    def test_invalid_inputs_report_errors(self) -> None:
        for arguments in (
            ("--time-limit", "0"),
            ("--max-expanded-nodes", "0"),
            ("--n-items", "0"),
            ("--n-items", "5", "--capacity-ratio", "2"),
            ("--dataset", "unsupported.txt"),
            ("--dataset", "missing_dataset.json"),
        ):
            with self.subTest(arguments=arguments):
                status, _, stderr = self.run_cli(*arguments)
                self.assertEqual(status, 2)
                self.assertIn("[Error]", stderr)


if __name__ == "__main__":
    unittest.main()
