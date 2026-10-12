"""Check that lesson visuals remain accessible, local, and curriculum-aligned.

These source checks run without MkDocs, a browser, or Azure. The documentation
builder checks the placement, captions, and full-size links in the staged site.
"""

from __future__ import annotations

import json
import math
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
ART_ROOT = ROOT / "docs" / "site-assets" / "learning-visuals"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SVG = "{" + SVG_NAMESPACE + "}"
STATIC_FILES = {
    "setup-tools.svg",
    "setup-context.svg",
    "setup-ownership.svg",
    "setup-cost-cleanup.svg",
    "setup-readiness.svg",
    "safe-run-loop.svg",
    "troubleshoot-loop.svg",
    "cleanup-boundary.svg",
}
LESSON_HEADINGS = (
    "## Objectives and checkpoints",
    "## Concept primer and design decisions",
    "## Read-only preflight",
    "## Deterministic break/fix exercise",
    "## Troubleshooting",
    "## Cleanup and residual verification",
)


def normalized_text(value: str) -> str:
    return " ".join(value.split())


def labs() -> list[tuple[Path, dict]]:
    folders = sorted((ROOT / "labs").glob("[0-2][0-9]-*"))
    return [
        (folder, yaml.safe_load((folder / "lab.yml").read_text(encoding="utf-8")))
        for folder in folders
        if folder.is_dir()
    ]


class LearningVisualsContract(unittest.TestCase):
    def test_all_lessons_have_stable_single_placement_anchors(self) -> None:
        lessons = labs()
        self.assertEqual(len(lessons), 28)
        for folder, metadata in lessons:
            with self.subTest(lab=metadata["id"]):
                readme = (folder / "README.md").read_text(encoding="utf-8")
                offsets = []
                for heading in LESSON_HEADINGS:
                    occurrences = list(re.finditer(r"^" + re.escape(heading) + r"$", readme, re.MULTILINE))
                    self.assertEqual(len(occurrences), 1, heading)
                    offsets.append(occurrences[0].start())
                self.assertEqual(offsets, sorted(offsets))
                tasks = re.findall(r"^## Task ([1-5]) — (.+) \{#task-([1-5])\}$", readme, re.MULTILINE)
                checkpoints = metadata["checkpoints"]
                self.assertEqual(len(checkpoints), 5)
                self.assertEqual(len(tasks), 5)
                for number, (task_number, title, anchor_number), checkpoint in zip(range(1, 6), tasks, checkpoints):
                    self.assertEqual(task_number, str(number))
                    self.assertEqual(anchor_number, str(number))
                    self.assertEqual(title, checkpoint["title"])

    def test_every_svg_has_resolvable_accessible_names_and_dimensions(self) -> None:
        paths = sorted(ART_ROOT.glob("*.svg"))
        self.assertEqual(len(paths), 36, "Expected 28 checkpoint roadmaps and eight shared/setup visuals")
        for path in paths:
            with self.subTest(asset=path.name):
                element = ET.fromstring(path.read_text(encoding="utf-8"))
                self.assertEqual(element.tag, SVG + "svg")
                self.assertEqual(element.get("role"), "img")
                ids = [item.get("id") for item in element.iter() if item.get("id")]
                self.assertEqual(len(ids), len(set(ids)), "SVG IDs must be unique")
                labelled_by = element.get("aria-labelledby", "").split()
                self.assertGreaterEqual(len(labelled_by), 2)
                accessible = {item.get("id"): item for item in element.iter() if item.get("id") in labelled_by}
                self.assertEqual(set(labelled_by), set(accessible))
                self.assertIn(SVG + "title", {item.tag for item in accessible.values()})
                self.assertIn(SVG + "desc", {item.tag for item in accessible.values()})
                for item in accessible.values():
                    self.assertTrue(normalized_text("".join(item.itertext())), "Accessible SVG descriptions must be nonempty")
                view_box = [float(value) for value in element.get("viewBox", "").split()]
                self.assertEqual(len(view_box), 4)
                self.assertTrue(all(math.isfinite(value) for value in view_box))
                self.assertGreater(view_box[2], 0)
                self.assertGreater(view_box[3], 0)

    def test_visuals_are_self_contained_and_have_no_active_content(self) -> None:
        paths = sorted(ART_ROOT.glob("*.svg"))
        self.assertEqual(len(paths), 36)
        forbidden_elements = {
            "script", "foreignObject", "iframe", "object", "embed", "audio", "video",
            "animate", "animateMotion", "animateTransform", "set",
        }
        for path in paths:
            with self.subTest(asset=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotRegex(source, r"(?i)<\?xml-stylesheet\b|<!DOCTYPE\b|<!ENTITY\b")
                element = ET.fromstring(source)
                ids = {item.get("id") for item in element.iter() if item.get("id")}
                for item in element.iter():
                    local_name = item.tag.rsplit("}", 1)[-1]
                    self.assertNotIn(local_name, forbidden_elements)
                    for attribute, value in item.attrib.items():
                        attribute_name = attribute.rsplit("}", 1)[-1].casefold()
                        self.assertFalse(attribute_name.startswith("on"), "Inline SVG event handlers are prohibited")
                        if attribute_name in {"href", "src"}:
                            self.assertTrue(value.startswith("#"), "SVG resources must be local fragment references")
                            self.assertIn(value[1:], ids, "SVG fragment reference must resolve")
                        self.assertNotRegex(value, r"(?i)javascript:|@import|expression\s*\(")
                        for reference in re.findall(r"url\(\s*['\"]?([^)'\"]+)", value, re.IGNORECASE):
                            self.assertTrue(reference.startswith("#"), "SVG paint references must be local")
                            self.assertIn(reference[1:], ids)
                    if local_name == "style":
                        styles = "".join(item.itertext())
                        self.assertNotRegex(styles, r"(?i)@import|javascript:|expression\s*\(")
                        for reference in re.findall(r"url\(\s*['\"]?([^)'\"]+)", styles, re.IGNORECASE):
                            self.assertTrue(reference.startswith("#"), "SVG styles cannot load remote resources")
                            self.assertIn(reference[1:], ids)

    def test_expected_setup_and_shared_visuals_exist(self) -> None:
        existing = {path.name for path in ART_ROOT.glob("*.svg")}
        expected = STATIC_FILES | {f"LAB-{number:02d}-roadmap.svg" for number in range(28)}
        self.assertEqual(existing, expected)

    def test_all_roadmaps_preserve_five_authoritative_checkpoint_records(self) -> None:
        for folder, metadata in labs():
            with self.subTest(lab=metadata["id"]):
                path = ART_ROOT / f"{metadata['id']}-roadmap.svg"
                element = ET.fromstring(path.read_text(encoding="utf-8"))
                self.assertEqual(element.get("data-lab-id"), metadata["id"])
                records = element.findall(SVG + "metadata")
                self.assertEqual(len(records), 1)
                record = json.loads(records[0].text or "")
                self.assertEqual(record["labId"], metadata["id"])
                self.assertEqual(record["title"], metadata["title"])
                self.assertEqual(record["domain"], metadata["domain"])
                self.assertEqual(record["status"], metadata["status"])
                self.assertEqual(record["source"], (folder / "README.md").relative_to(ROOT).as_posix())
                self.assertEqual(record["metadataSource"], (folder / "lab.yml").relative_to(ROOT).as_posix())
                checkpoint_groups = [item for item in element.iter() if item.get("data-checkpoint-id")]
                checkpoints = metadata["checkpoints"]
                self.assertEqual(len(record["tasks"]), 5)
                self.assertEqual(len(checkpoint_groups), 5)
                descriptions = normalized_text(" ".join(item.text or "" for item in element.findall(SVG + "desc")))
                for number, source_checkpoint, checkpoint_record, group in zip(range(1, 6), checkpoints, record["tasks"], checkpoint_groups):
                    for field in ("id", "title", "purpose", "expectedState", "objectiveIds"):
                        self.assertEqual(checkpoint_record[field], source_checkpoint[field], field)
                    self.assertEqual(checkpoint_record["number"], number)
                    self.assertEqual(checkpoint_record["anchor"], f"#task-{number}")
                    self.assertEqual(group.get("data-task"), str(number))
                    self.assertEqual(group.get("data-checkpoint-id"), source_checkpoint["id"])
                    visible_text = normalized_text(" ".join(group.itertext()))
                    self.assertIn(source_checkpoint["id"], visible_text)
                    self.assertIn(normalized_text(source_checkpoint["title"]), visible_text)
                    self.assertIn(source_checkpoint["id"], descriptions)
                    self.assertIn(normalized_text(source_checkpoint["title"]), descriptions)


if __name__ == "__main__":
    unittest.main()
