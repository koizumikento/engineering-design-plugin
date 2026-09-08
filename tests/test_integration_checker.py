import tempfile
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.integration_checker import (
    check_height_clearance,
    check_bottom_clearance,
    check_mounting_holes,
    check_pcb_clearance,
    overall_status,
    parse_spec_file,
    PCBSpec,
    EnclosureSpec,
)


class IntegrationCheckerTests(unittest.TestCase):
    def test_bottom_gap_reports_missing_contact_and_interference(self):
        enclosure = EnclosureSpec(boss_height=4)
        for height, required, expected in (
            (None, 1, "NOT_EVALUATED"),
            (6, 1, "FAIL"),
            (4, 1, "FAIL"),
            (3, 1, "PASS"),
            (0, 1, "PASS"),
            (3, None, "CONDITIONAL"),
            (-1, 1, "ERROR"),
            (3, -1, "ERROR"),
            (float("inf"), 1, "ERROR"),
        ):
            with self.subTest(height=height, required=required):
                self.assertEqual(check_bottom_clearance(PCBSpec(bottom_component_height=height), enclosure, required).status, expected)

    def test_bottom_interference_fails_the_documented_cli(self):
        content = """
### 基板仕様
| 基板サイズ | 40 x 20 mm |
| 基板厚 | 1.6 mm |
| 最大部品高 | 6 mm |
| 下面最大部品高 | 6 mm |
### 筐体仕様
| 内寸 | 44 x 24 x 13 mm |
| ボス高さ | 4 mm |
### Acceptance thresholds
| 下面最小クリアランス | 1 mm |
"""
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / "probe.md"
            spec.write_text(content, encoding="utf-8")
            run = subprocess.run(
                [sys.executable, "-X", "utf8", "scripts/integration_checker.py", str(spec), "-o", directory, "--json", "--fail-on-fail"],
                capture_output=True, text=True, encoding="utf-8", check=False,
            )
        self.assertEqual(run.returncode, 2, run.stderr)
        data = json.loads(run.stdout[run.stdout.index("{"):])
        self.assertEqual(data["overall_status"], "FAIL")
        bottom = next(row for row in data["checks"] if row["name"] == "下面クリアランス")
        self.assertEqual(bottom["details"]["bottom_gap_mm"], -2)

    def test_existing_iot_spec_parses_heights_and_bosses(self):
        pcb, enclosure, _ = parse_spec_file(
            Path("examples/iot-device/specs/iot-device-integrated-spec.md")
        )
        self.assertEqual((pcb.width, pcb.depth), (70.0, 40.0))
        self.assertEqual(pcb.max_component_height, 8.0)
        self.assertEqual(len(pcb.mounting_holes), 4)
        self.assertEqual(pcb.mounting_holes, enclosure.boss_positions)

    def test_missing_template_values_never_pass(self):
        pcb, enclosure, criteria = parse_spec_file(Path("templates/spec/integrated-spec.md"))
        results = [
            check_pcb_clearance(pcb, enclosure, criteria.xy_clearance),
            check_height_clearance(pcb, enclosure, criteria.top_clearance),
            check_mounting_holes(pcb, enclosure, criteria.mounting_tolerance),
        ]
        self.assertEqual(overall_status(results), "CONDITIONAL")
        self.assertTrue(all(result.status == "NOT_EVALUATED" for result in results))

    def test_negative_coordinates_and_spec_criteria(self):
        markdown = """
### 基板仕様
| 項目 | 値 |
|---|---|
| 基板サイズ | 40 x 20 mm |
| 基板厚 | 1.6 mm |
| 取付穴位置 | (-15, -5), (15, -5), (-15, 5), (15, 5) |
| 最大部品高 | 6.0 mm |

### 筐体仕様
| 項目 | 値 |
|---|---|
| 内寸 | 44 x 24 x 13 mm |
| ボス位置 | (-15, -5), (15, -5), (-15, 5), (15, 5) |
| ボス高さ | 4.0 mm |

### Acceptance thresholds
| 項目 | 値 |
|---|---|
| 基板外周最小クリアランス | 1.5 mm |
| 上面最小クリアランス | 2.0 mm |
| 取付位置許容差 | 0.2 mm |
"""
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / "integrated-spec.md"
            spec.write_text(markdown, encoding="utf-8")
            pcb, enclosure, criteria = parse_spec_file(spec)

        results = [
            check_pcb_clearance(pcb, enclosure, criteria.xy_clearance),
            check_height_clearance(pcb, enclosure, criteria.top_clearance),
            check_mounting_holes(pcb, enclosure, criteria.mounting_tolerance),
        ]
        self.assertEqual([result.status for result in results], ["PASS", "FAIL", "CONDITIONAL"])


if __name__ == "__main__":
    unittest.main()
