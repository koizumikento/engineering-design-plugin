"""Tests for the build123d STEP inspection CLI."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
INSPECT = REPO_ROOT / "scripts" / "cad_inspect.py"


@unittest.skipUnless(
    RUNTIME_PYTHON.is_file(),
    "root build123d runtime is not synced",
)
class CadInspectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from build123d import (
            Align,
            Axis,
            Box,
            Compound,
            Cylinder,
            Location,
            export_step,
        )

        cls.temporary_directory = tempfile.TemporaryDirectory(
            prefix="str236-cad-inspect-"
        )
        cls.output = Path(cls.temporary_directory.name)

        simple = Box(
            20,
            10,
            6,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        simple.label = "simple"
        cls.simple_step = cls.output / "simple.step"
        export_step(simple, cls.simple_step)

        body = Box(
            30,
            20,
            10,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        vertical_a = Cylinder(2, 14).move(Location((-7, 0, -2)))
        vertical_b = Cylinder(2, 14).move(Location((7, 0, -2)))
        horizontal = Cylinder(1.5, 34).rotate(Axis.Y, 90).move(Location((-17, 0, 5)))
        multi_axis = body - vertical_a - vertical_b - horizontal
        multi_axis.label = "multi_axis_holes"
        cls.multi_axis_step = cls.output / "multi-axis.step"
        export_step(multi_axis, cls.multi_axis_step)

        outer = Box(
            30,
            20,
            10,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        inner = Box(
            24,
            14,
            9,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ).move(Location((0, 0, 2)))
        cavity = outer - inner
        cavity.label = "open_cavity"
        cls.cavity_step = cls.output / "cavity.step"
        export_step(cavity, cls.cavity_step)

        base = Box(
            20,
            12,
            4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        base.label = "base"
        lid = Box(
            10,
            8,
            2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        lid.label = "lid"
        lid.location = Location((5, 0, 8))
        assembly = Compound(children=[base, lid], label="fixture_assembly")
        cls.assembly_step = cls.output / "assembly.step"
        export_step(assembly, cls.assembly_step)

        moved_base = Box(
            20,
            12,
            4,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        moved_base.label = "base"
        moved_lid = Box(
            10,
            8,
            2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        moved_lid.label = "lid"
        moved_lid.location = Location((6, 0, 8))
        moved_assembly = Compound(
            children=[moved_base, moved_lid],
            label="fixture_assembly",
        )
        cls.moved_assembly_step = cls.output / "assembly-moved.step"
        export_step(moved_assembly, cls.moved_assembly_step)

        duplicate_a = Box(2, 2, 2)
        duplicate_a.label = "duplicate"
        duplicate_b = Box(2, 2, 2).move(Location((4, 0, 0)))
        duplicate_b.label = "duplicate"
        duplicates = Compound(
            children=[duplicate_a, duplicate_b],
            label="duplicates",
        )
        cls.duplicate_step = cls.output / "duplicates.step"
        export_step(duplicates, cls.duplicate_step)

        before = Box(
            20,
            10,
            6,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        after = Box(
            24,
            10,
            6,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        cls.before_step = cls.output / "before.step"
        cls.after_step = cls.output / "after.step"
        export_step(before, cls.before_step)
        export_step(after, cls.after_step)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary_directory.cleanup()

    def run_cli(
        self,
        *arguments: str | Path,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(RUNTIME_PYTHON), str(INSPECT), *(str(item) for item in arguments)],
            cwd=REPO_ROOT,
            check=check,
            capture_output=True,
            text=True,
        )

    def run_json(self, *arguments: str | Path) -> dict:
        return json.loads(self.run_cli(*arguments).stdout)

    def test_refs_enumerates_local_selectors_and_major_planes(self) -> None:
        payload = self.run_json("refs", self.simple_step, "--topology")

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["artifact"]["units"], "mm")
        self.assertEqual(payload["artifact"]["runtime"]["build123d"], "0.11.1")
        self.assertEqual(len(payload["occurrences"]), 1)
        self.assertEqual(len(payload["solids"]), 1)
        self.assertEqual(payload["solids"][0]["selector"], "#o1.s1")
        self.assertEqual(payload["solids"][0]["aliases"], ["#s1"])
        self.assertEqual(len(payload["faces"]), 6)
        self.assertTrue(payload["major_planes"])
        self.assertIn("artifact-local", payload["selector_stability"])
        repeated = self.run_json("refs", self.simple_step, "--topology")
        self.assertEqual(
            [item["selector"] for item in payload["faces"]],
            [item["selector"] for item in repeated["faces"]],
        )

    def test_refs_cover_multi_axis_holes_and_internal_cavity(self) -> None:
        holes = self.run_json("refs", self.multi_axis_step, "--topology")
        cylindrical_axes = {
            axis
            for item in holes["faces"]
            if item["geometry_type"] == "cylinder"
            for axis in ("x", "z")
            if abs(item["axis"]["direction"][axis]) > 0.9
        }
        cavity = self.run_json("refs", self.cavity_step, "--topology")

        self.assertGreaterEqual(len(cylindrical_axes), 2)
        self.assertGreater(cavity["artifact"]["inspection"]["topology"]["faces"], 6)
        self.assertLess(cavity["artifact"]["inspection"]["volume"], 30 * 20 * 10)

    def test_measure_bbox_extent_and_face_distance(self) -> None:
        extent = self.run_json(
            "measure",
            self.simple_step,
            "--from",
            "#s1",
            "--extent",
            "x",
            "--expected",
            "20",
            "--tolerance",
            "0.000001",
        )
        refs = self.run_json("refs", self.simple_step, "--topology")
        bottom = next(
            item for item in refs["faces"] if item.get("normal", {}).get("z") == -1
        )
        top = next(
            item for item in refs["faces"] if item.get("normal", {}).get("z") == 1
        )
        distance = self.run_json(
            "measure",
            self.simple_step,
            "--from",
            bottom["selector"],
            "--to",
            top["selector"],
            "--axis",
            "z",
            "--expected",
            "6",
        )

        self.assertTrue(extent["measurement"]["passed"])
        self.assertEqual(extent["measurement"]["actual"], 20)
        self.assertTrue(distance["measurement"]["passed"])
        self.assertEqual(distance["measurement"]["center_offset"]["z"], 6)

    def test_align_center_and_flush_are_read_only(self) -> None:
        before_hash = self.assembly_step.read_bytes()
        center = self.run_json(
            "align",
            self.assembly_step,
            "--moving",
            "label:lid",
            "--target",
            "label:base",
            "--mode",
            "center",
        )
        refs = self.run_json("refs", self.assembly_step, "--topology")
        base_top = next(
            item
            for item in refs["faces"]
            if item["occurrence_selector"] == "#o1.1"
            and item.get("normal", {}).get("z") == 1
        )
        lid_bottom = next(
            item
            for item in refs["faces"]
            if item["occurrence_selector"] == "#o1.2"
            and item.get("normal", {}).get("z") == -1
        )
        flush = self.run_json(
            "align",
            self.assembly_step,
            "--moving",
            lid_bottom["selector"],
            "--target",
            base_top["selector"],
            "--mode",
            "flush",
            "--axis",
            "z",
        )

        self.assertEqual(
            center["alignment"]["translation_delta"],
            {"x": -5.0, "y": 0.0, "z": -7.0},
        )
        self.assertEqual(flush["alignment"]["translation_delta"]["z"], -4)
        self.assertTrue(flush["alignment"]["read_only"])
        self.assertEqual(self.assembly_step.read_bytes(), before_hash)

    def test_align_coaxial_returns_transverse_delta(self) -> None:
        refs = self.run_json("refs", self.multi_axis_step, "--topology")
        cylinders = [
            item
            for item in refs["faces"]
            if item["geometry_type"] == "cylinder"
            and abs(item["axis"]["direction"]["z"]) > 0.9
        ]
        self.assertGreaterEqual(len(cylinders), 2)
        coaxial = self.run_json(
            "align",
            self.multi_axis_step,
            "--moving",
            cylinders[0]["selector"],
            "--target",
            cylinders[1]["selector"],
            "--mode",
            "coaxial",
            "--axis",
            "z",
        )

        delta = coaxial["alignment"]["translation_delta"]
        self.assertEqual(delta["z"], 0)
        self.assertGreater(
            abs(delta["x"]) + abs(delta["y"]),
            0,
        )
        self.assertTrue(coaxial["alignment"]["vector_relation"]["parallel"])

    def test_frame_reports_component_and_selector_world_data(self) -> None:
        component = self.run_json("frame", self.assembly_step, "label:lid")
        refs = self.run_json("refs", self.multi_axis_step, "--topology")
        cylinder = next(
            item for item in refs["faces"] if item["geometry_type"] == "cylinder"
        )
        face = self.run_json(
            "frame",
            self.multi_axis_step,
            cylinder["selector"],
        )

        self.assertEqual(component["selection"]["selector"], "#o1.2")
        self.assertEqual(
            component["world_frame"]["position"],
            {"x": 5.0, "y": 0.0, "z": 8.0},
        )
        self.assertIsNotNone(face["world_frame"]["selection_axis"])

    def test_diff_reports_geometry_and_plane_changes(self) -> None:
        payload = self.run_json("diff", self.before_step, self.after_step)
        diff = payload["diff"]

        self.assertTrue(diff["changed"])
        self.assertEqual(diff["bounding_box_delta"]["x_len"], 4)
        self.assertEqual(diff["volume_delta"], 240)
        self.assertGreater(
            diff["major_planes"]["added_count"] + diff["major_planes"]["removed_count"],
            0,
        )

    def test_diff_reports_component_transform_changes(self) -> None:
        payload = self.run_json(
            "diff",
            self.assembly_step,
            self.moved_assembly_step,
        )
        lid = next(
            item
            for item in payload["diff"]["component_transforms"]
            if item["selector"] == "#o1.2"
        )

        self.assertEqual(lid["change"], "changed")
        self.assertEqual(lid["left_label"], "lid")
        self.assertEqual(lid["right_label"], "lid")
        self.assertEqual(lid["position_delta"]["x"], 1)

    def test_missing_and_ambiguous_selectors_fail_explicitly(self) -> None:
        missing = self.run_cli(
            "frame",
            self.simple_step,
            "#o1.s99",
            check=False,
        )
        ambiguous = self.run_cli(
            "frame",
            self.duplicate_step,
            "label:duplicate",
            check=False,
        )

        self.assertEqual(missing.returncode, 2)
        self.assertIn("did not resolve", missing.stderr)
        self.assertEqual(ambiguous.returncode, 2)
        self.assertIn("ambiguous", ambiguous.stderr)

    def test_text_output_is_available_without_replacing_json_contract(self) -> None:
        completed = self.run_cli(
            "measure",
            self.simple_step,
            "--from",
            "#s1",
            "--extent",
            "z",
            "--format",
            "text",
        )
        self.assertIn("bounding_box_extent: 6 mm", completed.stdout)


if __name__ == "__main__":
    unittest.main()
