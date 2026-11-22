"""
Cars Intelligence 2025 - Pages 00_Home, 03_ValueIntelligence, 04_VehicleExplorer & Intro Landing Page Test Suite
"""

import json
import os
import re
import unittest

from tests.helpers import (
    REPO_ROOT,
    REPORT_DEF_DIR,
    check_bounding_box_overlap,
    extract_visual_bindings,
    load_home_page,
    load_market_overview_page,
    load_performance_lab_page,
    load_semantic_model,
    load_value_intelligence_page,
    load_vehicle_explorer_page,
)


class TestPagesAndIntro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_semantic_model()
        cls.page0 = load_home_page()
        cls.page1 = load_market_overview_page()
        cls.page2 = load_performance_lab_page()
        cls.page3 = load_value_intelligence_page()
        cls.page4 = load_vehicle_explorer_page()
        cls.new_bento_pages = [
            ("03_ValueIntelligence", cls.page3),
            ("04_VehicleExplorer", cls.page4),
        ]
        cls.all_new_pages = [
            ("00_Home", cls.page0),
            ("03_ValueIntelligence", cls.page3),
            ("04_VehicleExplorer", cls.page4),
        ]

    def test_pages_metadata_order_and_active_home(self):
        """Verify pages.json includes 00_Home, 01-04 analytical pages, _QA_DAX_Profiling, and activates 00_Home."""
        pages_meta_path = os.path.join(REPORT_DEF_DIR, "pages", "pages.json")
        with open(pages_meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(
            meta.get("pageOrder"),
            [
                "a001c6b7a0e103746570",
                "3f7688a2cc2e12e049b0",
                "deb9f8692d454328e800",
                "c033c6b7a0e103746573",
                "d044c6b7a0e103746574",
                "cc13e0f0e1275c59bbe4",
            ],
        )
        self.assertEqual(meta.get("activePageName"), "a001c6b7a0e103746570")

    def test_new_pages_bento_geometry_and_zero_collisions(self):
        """Verify 00_Home (12 minimal Light Theme visuals) and 03/04 (15 Bento visuals) obey 1920x1080 with zero collisions."""
        expected_bento_types = {
            "cardVisual": 4,
            "slicer": 4,
            "gauge": 1,
            "clusteredBarChart": 1,
            "scatterChart": 1,
            "pivotTable": 1,
            "tableEx": 1,
            "textbox": 1,
            "pageNavigator": 1,
        }
        expected_home_types = {
            "textbox": 3,
            "pageNavigator": 1,
            "cardVisual": 4,
            "actionButton": 4,
        }
        nav1 = next(v for v in self.page1.visuals if v.visual_type == "pageNavigator")
        for label, page in self.all_new_pages:
            self.assertEqual(page.display_name, label)
            self.assertEqual(page.width, 1920, f"{label} width != 1920")
            self.assertEqual(page.height, 1080, f"{label} height != 1080")
            self.assertEqual(page.data.get("displayOption"), "FitToPage")
            exp_count = 12 if label == "00_Home" else 15
            exp_types = expected_home_types if label == "00_Home" else expected_bento_types
            self.assertEqual(len(page.visuals), exp_count, f"{label} expected {exp_count} visuals")

            actual_types = {}
            for v in page.visuals:
                actual_types[v.visual_type] = actual_types.get(v.visual_type, 0) + 1
                self.assertGreaterEqual(v.x, 0, f"{label}:{v.id} x < 0")
                self.assertGreaterEqual(v.y, 0, f"{label}:{v.id} y < 0")
                self.assertLessEqual(v.right, 1920, f"{label}:{v.id} right > 1920")
                self.assertLessEqual(v.bottom, 1080, f"{label}:{v.id} bottom > 1080")
            self.assertEqual(actual_types, exp_types, f"{label} visual type mismatch")

            for i in range(len(page.visuals)):
                for j in range(i + 1, len(page.visuals)):
                    self.assertFalse(
                        check_bounding_box_overlap(page.visuals[i], page.visuals[j]),
                        f"{label} overlap: {page.visuals[i].id} vs {page.visuals[j].id}",
                    )

            nav = next(v for v in page.visuals if v.visual_type == "pageNavigator")
            self.assertEqual((nav.x, nav.y, nav.width, nav.height), (nav1.x, nav1.y, nav1.width, nav1.height))

    def test_new_pages_all_bindings_resolve_in_tmdl(self):
        """Verify 100% of measure and column bindings on pages 00, 03, and 04 resolve cleanly in TMDL."""
        for label, page in self.all_new_pages:
            for v in page.visuals:
                bindings = extract_visual_bindings(v.data)
                for b_type, entity, prop in bindings:
                    self.assertIn(entity, self.model.tables, f"{label}:{v.id} missing table {entity}")
                    if b_type == "Measure":
                        self.assertIn(prop, self.model.tables[entity].measures, f"{label}:{v.id} missing measure {prop}")
                    else:
                        self.assertIn(prop, self.model.tables[entity].columns, f"{label}:{v.id} missing column {prop}")

    def test_home_page_specific_kpis_and_visuals(self):
        """Verify 00_Home Light Theme minimal layout, 4 KPIs, and 4 PageNavigation actionButtons linking to pages 01-04."""
        bg_val = self.page0.data.get("objects", {}).get("background", [{}])[0].get("properties", {}).get("color", {}).get("solid", {}).get("color", {}).get("expr", {}).get("Literal", {}).get("Value")
        self.assertEqual(bg_val, "'#F8FAFC'")

        all_bindings = set()
        nav_targets = set()
        for v in self.page0.visuals:
            all_bindings.update(extract_visual_bindings(v.data))
            if v.visual_type == "actionButton":
                links = v.data.get("visual", {}).get("visualContainerObjects", {}).get("visualLink", [])
                for lk in links:
                    props = lk.get("properties", {})
                    if props.get("type", {}).get("expr", {}).get("Literal", {}).get("Value") == "'PageNavigation'":
                        nav_targets.add(props.get("navigationSection", {}).get("expr", {}).get("Literal", {}).get("Value", "").strip("'"))

        self.assertEqual(
            nav_targets,
            {"3f7688a2cc2e12e049b0", "deb9f8692d454328e800", "c033c6b7a0e103746573", "d044c6b7a0e103746574"},
        )
        for m in ("Vehicle Count", "Company Count", "Electrified Share %", "Underpriced Gems Count"):
            self.assertIn(("Measure", "_Measures", m), all_bindings)

    def test_value_intelligence_specific_kpis_and_hedonic_visuals(self):
        """Verify 03_ValueIntelligence binds to hedonic pricing, ROI, and value measures with TopN and gradient."""
        all_bindings = set()
        for v in self.page3.visuals:
            all_bindings.update(extract_visual_bindings(v.data))
        for m in ("Value Index", "Value Index (AVG Market)", "HP per 10k USD", "Price per HP", "Underpriced Gems Count", "Hedonic Fair Price", "Average Price", "Hedonic Price Gap %"):
            self.assertIn(("Measure", "_Measures", m), all_bindings)
        pivot = next(v for v in self.page3.visuals if v.visual_type == "pivotTable")
        self.assertIn("linearGradient2", json.dumps(pivot.data))
        table = next(v for v in self.page3.visuals if v.visual_type == "tableEx")
        self.assertIn("TopN", json.dumps(table.data))

    def test_vehicle_explorer_specific_kpis_and_dossier(self):
        """Verify 04_VehicleExplorer binds to engineering density, price percentile, and dossier specification measures."""
        all_bindings = set()
        for v in self.page4.visuals:
            all_bindings.update(extract_visual_bindings(v.data))
        for m in ("Specific Output (HP/L)", "EV Power Density (HP/kWh)", "Electrified Share %", "Data Quality Rate %", "Score Price (inverted)", "Performance Index", "Score HP", "Score Acceleration", "Average Torque"):
            self.assertIn(("Measure", "_Measures", m), all_bindings)
        self.assertIn(("Column", "FactVehicle", "Vehicle Display Name"), all_bindings)
        self.assertIn(("Column", "FactVehicle", "Seats_Layout"), all_bindings)

    def test_introductory_landing_page_html_integrity(self):
        """Verify html/index.html is UTF-8 without BOM, links all 4 pages + PBIP, and embeds real car images."""
        html_path = os.path.join(REPO_ROOT, "html", "index.html")
        self.assertTrue(os.path.isfile(html_path), "html/index.html must exist")
        with open(html_path, "rb") as f:
            raw = f.read()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "html/index.html must not contain UTF-8 BOM")
        text = raw.decode("utf-8")

        for token in (
            "00_Home",
            "01_MarketOverview",
            "02_PerformanceLab",
            "03_ValueIntelligence",
            "04_VehicleExplorer",
            "#page-01",
            "#page-02",
            "#page-03",
            "#page-04",
            "CarsIntelligence.pbip",
            "Cars Intelligence 2025",
        ):
            self.assertIn(token, text)

        img_urls = re.findall(r'<img\b[^>]*\bsrc="(https://[^"]+)"', text)
        self.assertGreaterEqual(len(img_urls), 6, "Expected at least 6 real car image tags in html/index.html")
        self.assertNotIn("\\$", text, "html/index.html should not contain escaped dollar signs")


if __name__ == "__main__":
    unittest.main()
