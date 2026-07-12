import tempfile
import unittest
from pathlib import Path

from scripts.integration_checker import (
    check_height_clearance,
    check_mounting_holes,
    check_pcb_clearance,
    overall_status,
    parse_spec_file,
)


class IntegrationCheckerTests(unittest.TestCase):
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
