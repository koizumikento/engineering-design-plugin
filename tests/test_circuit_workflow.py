"""Exercise ERC failure propagation and native schematic generation without KiCad installed."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills/circuit-design/scripts"
SYMBOL_LIBRARY = '''(kicad_symbol_lib (version 20220914) (generator "test")
  (symbol "R" (in_bom yes) (on_board yes)
    (property "Reference" "R" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
    (property "Value" "R" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
    (symbol "R_0_1"
      (rectangle (start -2.54 1.27) (end 2.54 -1.27)
        (stroke (width 0.254) (type default)) (fill (type none))))
    (symbol "R_1_1"
      (pin passive line (at -5.08 0 0) (length 2.54)
        (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 5.08 0 180) (length 2.54)
        (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27))))))))
)'''


class CircuitWorkflowTests(unittest.TestCase):
    def run_cli(self, root, entrypoint, source, *args):
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        env.update({f"KICAD{version}_SYMBOL_DIR": str(root / "symbols") for version in (9, 10)})
        return subprocess.run(
            [sys.executable, str(SCRIPTS / entrypoint), str(source), "-o", str(root / "out"), *args],
            cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", check=False,
        )

    def test_erc_failure_and_skip_propagate_to_reports_and_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "circuit.py"
            for assertion, extra, code, status in (
                ("False", (), 2, False), ("True", (), 0, True),
                ("False", ("--no-erc",), 0, None),
            ):
                with self.subTest(assertion=assertion, extra=extra):
                    source.write_text(f"from skidl import erc_assert\nerc_assert('{assertion}', 'review assertion')\n", encoding="utf-8")
                    run = self.run_cli(root, "skidl_runner.py", source, "--json", *extra)
                    self.assertEqual(run.returncode, code, run.stderr)
                    result = json.loads(run.stdout[run.stdout.index("{"):])
                    self.assertIs(result["erc"].get("passed"), status)
                    if status is False:
                        self.assertTrue(any("review assertion" in msg for msg in result["erc"]["errors"]))
                        self.assertIn("`FAILED`", (root / "out/reports/circuit-erc-summary.md").read_text(encoding="utf-8"))
                    if status is None:
                        self.assertIn("`SKIPPED`", (root / "out/reports/circuit-erc-summary.md").read_text(encoding="utf-8"))

    def test_native_no_output_cannot_reuse_a_stale_schematic(self):
        sys.path.insert(0, str(SCRIPTS))
        try:
            from kicad_sch_export import export_native_schematic
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "old.kicad_sch"
                target.write_text("old artifact", encoding="utf-8")
                circuit = SimpleNamespace(generate_schematic=lambda **kwargs: None)
                with self.assertRaisesRegex(RuntimeError, "did not generate"):
                    export_native_schematic(circuit, target, "kicad9")
                self.assertEqual(target.read_text(encoding="utf-8"), "old artifact")
        finally:
            sys.path.pop(0)

    def test_native_generates_parseable_schematic_for_both_targets(self):
        from simp_sexp import Sexp

        for version in (9, 10):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                symbols = root / "symbols"
                symbols.mkdir()
                (symbols / "review.kicad_sym").write_text(SYMBOL_LIBRARY, encoding="utf-8")
                (symbols / "power.kicad_sym").write_text('(kicad_symbol_lib (version 20220914) (generator "test"))', encoding="utf-8")
                source = root / "circuit.v1.py"
                source.write_text('''from skidl import Part, Net
a = Part("review", "R", value="1k", footprint="Test:R", tag="first")
b = Part("review", "R", value="2k", footprint="Test:R", tag="second")
x, y = Net("X"), Net("Y")
x += a[1], b[1]
y += a[2], b[2]
''', encoding="utf-8")
                name_args = ("--name", "board.rev2") if version == 10 else ()
                base_name = "board.rev2" if name_args else source.stem
                run = self.run_cli(root, "kicad_sch_export.py", source, "--kicad-version", str(version), *name_args)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                schematic = root / "out/kicad" / base_name / f"{base_name}.kicad_sch"
                parsed = Sexp(schematic.read_text(encoding="utf-8"))
                symbols = parsed.search("/kicad_sch/symbol")
                self.assertEqual(len(symbols), 2)
                references = {prop[2] for symbol in symbols for prop in symbol.search("/symbol/property") if prop[1] == "Reference"}
                self.assertEqual(references, {"R1", "R2"})


if __name__ == "__main__":
    unittest.main()
