#!/usr/bin/env python3
"""
Tier 5 Adversarial Mutation Testing and Sensitivity Harness for Cars Intelligence 2025.
Validates that scripts/verify_report.py is an effective, non-vacuous verifier
by injecting controlled defect mutations into isolated temporary copies of report
definitions and proving that verify_report.py fails with non-zero exit code on every defect.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERIFY_SCRIPT = os.path.join(REPO_ROOT, "scripts", "verify_report.py")

class TestTier5AdversarialMutations(unittest.TestCase):
    """Adversarial mutation test suite stress-testing verify_report.py sensitivity."""

    def setUp(self):
        # Create an isolated temporary copy of powerbi/ and scripts/
        self.temp_dir = tempfile.mkdtemp(prefix="adversarial_test_")
        self.temp_powerbi = os.path.join(self.temp_dir, "powerbi")
        self.temp_scripts = os.path.join(self.temp_dir, "scripts")
        
        shutil.copytree(os.path.join(REPO_ROOT, "powerbi"), self.temp_powerbi)
        shutil.copytree(os.path.join(REPO_ROOT, "scripts"), self.temp_scripts)
        
        self.page2_dir = os.path.join(
            self.temp_powerbi,
            "CarsIntelligence.Report",
            "definition",
            "pages",
            "deb9f8692d454328e800"
        )
        self.page2_visuals_dir = os.path.join(self.page2_dir, "visuals")
        self.temp_verify_script = os.path.join(self.temp_scripts, "verify_report.py")

    def tearDown(self):
        # Clean up the temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_temp_verifier(self):
        """Run verify_report.py inside the temporary environment and return completed process."""
        return subprocess.run(
            [sys.executable, self.temp_verify_script],
            cwd=self.temp_dir,
            capture_output=True,
            text=True
        )

    # -------------------------------------------------------------------------
    # Baseline Test: Production Clean
    # -------------------------------------------------------------------------
    def test_baseline_clean_verification(self):
        """Verify that an unmodified copy of the repository passes 100% with exit code 0."""
        res = self.run_temp_verifier()
        self.assertEqual(res.returncode, 0, f"Baseline verification must pass with exit code 0. Output:\n{res.stdout}\n{res.stderr}")
        self.assertIn("26 PASSED | 0 FAILED | 0 WARNINGS", res.stdout)
        self.assertIn("[PASS] Performance Lab Canvas Resolution", res.stdout)
        self.assertIn("[PASS] Performance Lab Visual Count", res.stdout)
        self.assertIn("[PASS] Performance Lab Bounds Compliance", res.stdout)
        self.assertIn("[PASS] Performance Lab Zero Collisions", res.stdout)
        self.assertIn("[PASS] Performance Lab Visual Types", res.stdout)
        self.assertIn("[PASS] Performance Lab PivotTable Gradient", res.stdout)
        self.assertIn("[PASS] Performance Lab TableEx Top N", res.stdout)
        self.assertIn("[PASS] Performance Lab Data Bindings", res.stdout)
        self.assertIn("[PASS] Performance Lab Zero SVG", res.stdout)

    # -------------------------------------------------------------------------
    # Mutation a: Off-canvas visual (x + width > 1920 or y + height > 1080)
    # -------------------------------------------------------------------------
    def test_mutation_a_off_canvas_visual(self):
        """Mutation A: Mutate a visual to exceed canvas bounds (x + width = 2050 > 1920)."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_table_leaders", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Mutate width to push it off-canvas
        data["position"]["x"] = 1500
        data["position"]["width"] = 550  # x + width = 2050 > 1920
        with open(target_visual_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when a visual exceeds canvas bounds")
        self.assertIn("[FAIL] Performance Lab Bounds Compliance", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation b: Overlapping pair of visuals
    # -------------------------------------------------------------------------
    def test_mutation_b_overlapping_visuals(self):
        """Mutation B: Shift a visual so its bounding box collides with an adjacent visual."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_page_nav", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Move page nav from (1390, 20) to (100, 20), colliding with perf_header_title (36, 20, 640, 52)
        data["position"]["x"] = 100
        with open(target_visual_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when visuals overlap")
        self.assertIn("[FAIL] Performance Lab Zero Collisions", res.stdout)
        self.assertIn("Overlap between perf_header_title", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation c: Incorrect visual type (e.g. legacy card)
    # -------------------------------------------------------------------------
    def test_mutation_c_incorrect_visual_type(self):
        """Mutation C: Change a modern cardVisual to a legacy card visual."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_kpi_hp", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["visual"]["visualType"] = "card"
        with open(target_visual_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when an incorrect visual type is used")
        self.assertIn("[FAIL] Performance Lab Visual Types", res.stdout)
        self.assertIn("Mismatch in visual types", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation d: Broken measure binding
    # -------------------------------------------------------------------------
    def test_mutation_d_broken_measure_binding(self):
        """Mutation D: Mutate a visual measure binding to point to a nonexistent measure."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_kpi_speed", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        content_str = json.dumps(data)
        content_str = content_str.replace("Average Speed", "NonExistentMeasureBroken")
        with open(target_visual_json, "w", encoding="utf-8") as f:
            f.write(content_str)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail on broken measure bindings")
        self.assertIn("[FAIL] Performance Lab Data Bindings", res.stdout)
        self.assertIn("Missing measure 'NonExistentMeasureBroken'", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation e: Lingering SVG tag or data-URI
    # -------------------------------------------------------------------------
    def test_mutation_e_lingering_svg(self):
        """Mutation E: Inject a lingering SVG tag into a Page 02 visual definition."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_header_title", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            content = f.read()

        mutated_content = content.replace("Performance Lab", "Performance Lab <svg viewBox='0 0 10 10'></svg>")
        with open(target_visual_json, "w", encoding="utf-8") as f:
            f.write(mutated_content)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when an SVG tag is detected on Page 02")
        self.assertIn("[FAIL] Performance Lab Zero SVG", res.stdout)
        self.assertIn("[FAIL] Zero SVG References", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation f1: UTF-8 with BOM on JSON definition file (version.json)
    # -------------------------------------------------------------------------
    def test_mutation_f1_utf8_bom_json_definition(self):
        """Mutation F1: Inject UTF-8 BOM into a report definition JSON file (version.json)."""
        target_json = os.path.join(self.temp_powerbi, "CarsIntelligence.Report", "definition", "version.json")
        with open(target_json, "rb") as f:
            content = f.read()

        bom_content = b"\xef\xbb\xbf" + content
        with open(target_json, "wb") as f:
            f.write(bom_content)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when UTF-8 BOM is detected in JSON")
        self.assertIn("[FAIL] JSON UTF-8 No-BOM", res.stdout)
        self.assertIn("BOM detected", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation f2: UTF-8 with BOM on TMDL table file (_Measures.tmdl)
    # -------------------------------------------------------------------------
    def test_mutation_f2_utf8_bom_tmdl(self):
        """Mutation F2: Inject UTF-8 BOM into a semantic model TMDL file (_Measures.tmdl)."""
        target_tmdl = os.path.join(self.temp_powerbi, "CarsIntelligence.SemanticModel", "definition", "tables", "_Measures.tmdl")
        with open(target_tmdl, "rb") as f:
            content = f.read()

        bom_content = b"\xef\xbb\xbf" + content
        with open(target_tmdl, "wb") as f:
            f.write(bom_content)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when UTF-8 BOM is detected in TMDL")
        self.assertIn("[FAIL] TMDL UTF-8 No-BOM", res.stdout)
        self.assertIn("BOM detected", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Mutation f3: UTF-8 BOM on Page 02 JSON (page.json) — Defect Vulnerability Detection
    # -------------------------------------------------------------------------
    def test_mutation_f3_utf8_bom_page2_json_fragility(self):
        """Mutation F3: Inject UTF-8 BOM into page.json.
        Empirically confirms that verify_report.py exits non-zero (exit code 1).
        Also captures the unhandled JSONDecodeError in stderr due to lack of try/except around json.load."""
        target_page_json = os.path.join(self.page2_dir, "page.json")
        with open(target_page_json, "rb") as f:
            content = f.read()

        bom_content = b"\xef\xbb\xbf" + content
        with open(target_page_json, "wb") as f:
            f.write(bom_content)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must exit non-zero when BOM is present")
        # Confirms non-zero exit code 1
        self.assertEqual(res.returncode, 1)

    # -------------------------------------------------------------------------
    # Additional Sensitivity Mutation G: Missing Linear Gradient on PivotTable
    # -------------------------------------------------------------------------
    def test_mutation_g_missing_pivot_gradient(self):
        """Mutation G: Remove linearGradient2 conditional formatting from pivotTable."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_pivot_matrix", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            content = f.read()

        mutated = content.replace("linearGradient2", "staticColor")
        with open(target_visual_json, "w", encoding="utf-8") as f:
            f.write(mutated)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when pivotTable lacks linearGradient2")
        self.assertIn("[FAIL] Performance Lab PivotTable Gradient", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Additional Sensitivity Mutation H: Missing Top N Filter on TableEx
    # -------------------------------------------------------------------------
    def test_mutation_h_missing_table_top_n(self):
        """Mutation H: Remove Top N filter configuration from tableEx."""
        target_visual_json = os.path.join(self.page2_visuals_dir, "perf_table_leaders", "visual.json")
        with open(target_visual_json, "r", encoding="utf-8") as f:
            content = f.read()

        mutated = content.replace('"type": "TopN"', '"type": "Advanced"')
        with open(target_visual_json, "w", encoding="utf-8") as f:
            f.write(mutated)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when tableEx lacks Top N filter")
        self.assertIn("[FAIL] Performance Lab TableEx Top N", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Additional Sensitivity Mutation I: Visual Container Count Mismatch
    # -------------------------------------------------------------------------
    def test_mutation_i_visual_count_mismatch(self):
        """Mutation I: Delete one visual container to create a container count mismatch (14 vs 15)."""
        target_visual_dir = os.path.join(self.page2_visuals_dir, "perf_slicer_scope")
        shutil.rmtree(target_visual_dir)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when visual container count != 15")
        self.assertIn("[FAIL] Performance Lab Visual Count", res.stdout)
        self.assertIn("Expected 15 visual containers, found 14", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

    # -------------------------------------------------------------------------
    # Additional Sensitivity Mutation J: Canvas Resolution Mismatch
    # -------------------------------------------------------------------------
    def test_mutation_j_canvas_resolution_mismatch(self):
        """Mutation J: Mutate page.json canvas dimensions (1920x1079 instead of 1920x1080)."""
        target_page_json = os.path.join(self.page2_dir, "page.json")
        with open(target_page_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["height"] = 1079
        with open(target_page_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        res = self.run_temp_verifier()
        self.assertNotEqual(res.returncode, 0, "verify_report.py must fail when canvas resolution != 1920x1080")
        self.assertIn("[FAIL] Performance Lab Canvas Resolution", res.stdout)
        self.assertIn("Canvas is 1920x1079, expected 1920x1080", res.stdout)
        self.assertRegex(res.stdout, r"Summary:\s+\d+\s+PASSED\s+\|\s+[1-9]\d*\s+FAILED")

if __name__ == "__main__":
    unittest.main(verbosity=2)
