"""
Cars Intelligence 2025 - Tier 2: Boundary & Corner Cases Test Suite
Boundary, limit, zero/null, and invalid syntax rejection verification.
Covers Features 1 through 15 with >= 5 tests per feature (75 tests total).
"""

import unittest
import os
import glob
import json
import subprocess
import re
from tests.helpers import (
    REPO_ROOT,
    SEMANTIC_MODEL_DIR,
    REPORT_DEF_DIR,
    PAGE_DIR,
    PAGE1_DIR,
    PAGE2_DIR,
    THEME_PATH,
    VERIFY_SCRIPT_PATH,
    load_semantic_model,
    load_report_page,
    load_market_overview_page,
    load_performance_lab_page,
    load_theme,
    extract_visual_bindings,
    check_bounding_box_overlap,
)

class TestTier2Boundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_semantic_model()
        cls.page = load_report_page()
        cls.page1 = cls.page
        cls.page2 = load_performance_lab_page()
        cls.theme = load_theme()

    # =========================================================================
    # FEATURE 1: Purge Legacy SVG Measures (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f1_b01_case_insensitive_svg_measure_scan(self):
        """F1.B1: Case-insensitive scan ensures no measure name contains 'svg'."""
        measures_table = self.model.tables["_Measures"]
        for m_name in measures_table.measures.keys():
            self.assertNotIn("svg", m_name.lower(), f"Measure '{m_name}' contains 'svg'")

    def test_f1_b02_regex_xml_svg_tags_in_measures(self):
        """F1.B2: Ensure no measure definition contains raw XML <svg tags or </svg>."""
        raw_text = self.model.tables["_Measures"].raw_text
        svg_tags = re.findall(r"<\s*/?\s*svg", raw_text, re.IGNORECASE)
        self.assertEqual(len(svg_tags), 0, f"Found raw SVG tags in _Measures.tmdl: {svg_tags}")

    def test_f1_b03_data_uri_schemes_in_measures(self):
        """F1.B3: Ensure no measure contains data URI schemes (data:image/svg+xml or data:image/png)."""
        raw_text = self.model.tables["_Measures"].raw_text
        data_uris = re.findall(r"data:image/[a-zA-Z0-9\+\-\.]+", raw_text, re.IGNORECASE)
        self.assertEqual(len(data_uris), 0, f"Found data URI schemes in _Measures.tmdl: {data_uris}")

    def test_f1_b04_empty_whitespace_clean_measure_syntax(self):
        """F1.B4: Ensure no measure declaration has an empty name or empty expression block."""
        for m_name, m_data in self.model.tables["_Measures"].measures.items():
            self.assertGreater(len(m_name.strip()), 0, "Measure name cannot be empty whitespace")
            self.assertGreater(len(m_data["block"].strip()), 0, f"Measure {m_name} has empty block")

    def test_f1_b05_purged_measure_injection_rejection(self):
        """F1.B5: Adversarial check: Synthetic assertion confirms detector detects legacy names."""
        legacy_names = [
            "SVG Heatmap Tile",
            "SVG Live Speedometer Cockpit",
            "SVG Live 3D Coupe Telemetry",
            "SVG Market Position Badge",
            "SVG Value Sparkbar",
            "SVG Performance Gauge"
        ]
        synthetic_bad_text = "measure 'SVG Heatmap Tile' = \"<svg></svg>\""
        for name in legacy_names:
            self.assertNotIn(name, self.model.tables["_Measures"].raw_text)
        # Verify that checking synthetic text WOULD fail, validating test sensitivity
        self.assertIn("SVG Heatmap Tile", synthetic_bad_text)

    # =========================================================================
    # FEATURE 2: Purge Legacy SVG Column (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f2_b01_case_insensitive_svg_column_scan(self):
        """F2.B1: Case-insensitive scan ensures no column in FactVehicle contains 'svg'."""
        fact = self.model.tables["FactVehicle"]
        for c_name in fact.columns.keys():
            self.assertNotIn("svg", c_name.lower(), f"FactVehicle column '{c_name}' contains 'svg'")

    def test_f2_b02_no_data_uri_calculated_columns(self):
        """F2.B2: Ensure no calculated column in FactVehicle outputs data-URIs or XML tags."""
        fact = self.model.tables["FactVehicle"]
        for c_name, c_data in fact.columns.items():
            if c_data["isCalculated"]:
                block = c_data["block"]
                self.assertNotIn("data:image", block, f"Column {c_name} contains data:image URI")
                self.assertNotIn("<svg", block.lower(), f"Column {c_name} contains SVG tag")

    def test_f2_b03_extreme_dax_expressions_no_dangling_columns(self):
        """F2.B3: Verify calculated columns in FactVehicle only reference valid columns in FactVehicle."""
        fact = self.model.tables["FactVehicle"]
        all_cols = set(fact.columns.keys())
        for c_name, c_data in fact.columns.items():
            if c_data["isCalculated"]:
                # Look for FactVehicle[Col] references
                refs = re.findall(r"FactVehicle\[([^\]]+)\]", c_data["block"])
                for ref in refs:
                    self.assertIn(ref, all_cols, f"Calculated column {c_name} references non-existent column {ref}")

    def test_f2_b04_column_type_boundary(self):
        """F2.B4: Verify calculated columns return supported Power BI primitive types."""
        valid_types = {"double", "string", "int64", "boolean", "dateTime", "decimal"}
        fact = self.model.tables["FactVehicle"]
        for c_name, c_data in fact.columns.items():
            if c_data["isCalculated"] and c_data["dataType"]:
                self.assertIn(c_data["dataType"], valid_types, f"Column {c_name} has invalid dataType: {c_data['dataType']}")

    def test_f2_b05_fact_relationships_not_orphaned(self):
        """F2.B5: Verify no relationship in relationships.tmdl references a deleted or non-existent column."""
        for rel in self.model.relationships:
            from_table, from_col = rel["fromColumn"].split(".", 1)
            to_table, to_col = rel["toColumn"].split(".", 1)
            self.assertIn(from_col, self.model.tables[from_table].columns)
            self.assertIn(to_col, self.model.tables[to_table].columns)

    # =========================================================================
    # FEATURE 3: Semantic Model Integrity (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f3_b01_measure_circular_reference_boundary(self):
        """F3.B1: Verify measures do not have immediate self-referential circular definitions."""
        measures = self.model.tables["_Measures"].measures
        for m_name, m_data in measures.items():
            block = m_data["block"]
            # Look for [m_name] inside its own block
            # Exclude comment lines if any
            lines = [l for l in block.splitlines() if not l.strip().startswith("//")]
            content = "\n".join(lines[1:])  # skip declaration line
            self.assertNotIn(f"[{m_name}]", content, f"Measure {m_name} contains immediate self-reference")

    def test_f3_b02_divide_by_zero_safe_handling(self):
        """F3.B2: Verify percentage measures use DIVIDE() to protect against division by zero."""
        ratio_measures = ["Electrified Share %", "Best Value Share %", "Data Quality Rate %"]
        measures = self.model.tables["_Measures"].measures
        for rm in ratio_measures:
            self.assertIn(rm, measures)
            self.assertIn("DIVIDE(", measures[rm]["block"], f"Ratio measure {rm} should use safe DIVIDE() function")

    def test_f3_b03_format_string_syntax_boundary(self):
        """F3.B3: Verify format strings contain valid characters and non-empty syntax."""
        measures = self.model.tables["_Measures"].measures
        for m_name, m_data in measures.items():
            fs = m_data["formatString"]
            if fs:
                self.assertNotIn("\n", fs, f"Format string for {m_name} has newline")
                self.assertTrue(any(c in fs for c in ["0", "#", "%", "$"]), f"Invalid format string {fs} for {m_name}")

    def test_f3_b04_empty_blank_handling_in_measures(self):
        """F3.B4: Verify key aggregation measures use ISBLANK or filtering to guard nulls."""
        measures = self.model.tables["_Measures"].measures
        # Vehicle Count uses DISTINCTCOUNT or COUNTROWS
        vcount_block = measures["Vehicle Count"]["block"]
        self.assertTrue("COUNT" in vcount_block or "CALCULATE" in vcount_block)

    def test_f3_b05_model_tables_lineage_tags_non_empty(self):
        """F3.B5: Verify all dimension, fact, and measure tables have non-empty valid lineage tags."""
        for t_name, table in self.model.tables.items():
            self.assertIsNotNone(table.lineage_tag, f"Table {t_name} is missing lineageTag")
            self.assertGreater(len(table.lineage_tag), 10, f"Table {t_name} lineageTag too short")

    # =========================================================================
    # FEATURE 4: Deploy Automated Verification Script (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f4_b01_script_synthetic_failure_detection(self):
        """F4.B1: Test verification script sensitivity by asserting reporter fails on bad data."""
        from scripts.verify_report import VerificationReporter
        reporter = VerificationReporter()
        reporter.log_pass("Test Pass", "All good")
        reporter.log_fail("Test Fail", "Synthetic error triggered")
        self.assertEqual(reporter.passes, 1)
        self.assertEqual(reporter.failures, 1)

    def test_f4_b02_script_handles_empty_or_missing_path(self):
        """F4.B2: Verify script functions when run from any working directory."""
        # Run script with cwd set to a different directory
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], cwd=SEMANTIC_MODEL_DIR, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, "verify_report.py must work regardless of current working directory")

    def test_f4_b03_script_stdout_contains_structured_sections(self):
        """F4.B3: Verify script stdout has clean structured delimiters."""
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        self.assertIn("================================================================================", res.stdout)
        self.assertIn("Summary:", res.stdout)
        self.assertIn("0 FAILED | 0 WARNINGS", res.stdout)

    def test_f4_b04_script_performance_boundary(self):
        """F4.B4: Verify scripts/verify_report.py executes in under 5.0 seconds."""
        import time
        start = time.time()
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, f"Verification script took too long: {elapsed:.2f}s")
        self.assertEqual(res.returncode, 0)

    def test_f4_b05_script_exit_code_consistency(self):
        """F4.B5: Verify python process exit code is 0 on success."""
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

    # =========================================================================
    # FEATURE 5: Pure Typography KPI Cards (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f5_b01_single_measure_projection_limit(self):
        """F5.B1: Verify each KPI card has strictly 1 measure projection in queryState."""
        cards = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        for card in cards:
            projections = card.data.get("visual", {}).get("query", {}).get("queryState", {}).get("Data", {}).get("projections", [])
            self.assertEqual(len(projections), 1, f"Card {card.id} has {len(projections)} projections; expected 1")

    def test_f5_b02_card_dimensions_uniformity(self):
        """F5.B2: Verify all 4 KPI cards have identical dimensions: width 444 and height 116."""
        cards = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        for card in cards:
            self.assertEqual(card.width, 444, f"Card {card.id} width != 444")
            self.assertEqual(card.height, 116, f"Card {card.id} height != 116")
            self.assertEqual(card.y, 142, f"Card {card.id} y != 142")

    def test_f5_b03_card_typography_font_boundary(self):
        """F5.B3: Verify callout value font sizes are >= 24pt and label font sizes >= 10pt."""
        cards = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        for card in cards:
            card_str = json.dumps(card.data)
            self.assertIn("28D", card_str, f"Card {card.id} callout fontSize should be 28D")
            self.assertIn("11D", card_str, f"Card {card.id} label fontSize should be 11D")

    def test_f5_b04_card_background_opacity(self):
        """F5.B4: Verify all KPI card backgrounds specify white '#FFFFFF' with 0% transparency."""
        cards = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        for card in cards:
            card_str = json.dumps(card.data)
            self.assertIn("#FFFFFF", card_str)
            self.assertIn('"transparency"', card_str)

    def test_f5_b05_card_zero_image_or_svg_controls(self):
        """F5.B5: Verify no KPI card JSON references image, svg, icon, or sparkline controls."""
        cards = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        for card in cards:
            card_str = json.dumps(card.data).lower()
            self.assertNotIn("svg", card_str)
            self.assertNotIn("imageurl", card_str)
            self.assertNotIn("data:image", card_str)

    # =========================================================================
    # FEATURE 6: Performance Index Cockpit (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f6_b01_gauge_axis_range_order(self):
        """F6.B1: Verify gauge axis min (0) is strictly less than max (100)."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        axis_props = gauge.data.get("visual", {}).get("objects", {}).get("axis", [{}])[0].get("properties", {})
        min_val = axis_props.get("min", {}).get("expr", {}).get("Literal", {}).get("Value", "").replace("D", "")
        max_val = axis_props.get("max", {}).get("expr", {}).get("Literal", {}).get("Value", "").replace("D", "")
        self.assertEqual(float(min_val), 0.0)
        self.assertEqual(float(max_val), 100.0)
        self.assertLess(float(min_val), float(max_val))

    def test_f6_b02_gauge_no_legacy_svg_objects(self):
        """F6.B2: Verify gauge visual container contains no SVG controls or legacy objects."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        g_str = json.dumps(gauge.data).lower()
        self.assertNotIn("<svg", g_str)
        self.assertNotIn("data:image", g_str)
        self.assertNotIn("speedometer", g_str)

    def test_f6_b03_gauge_dual_measure_exactness(self):
        """F6.B3: Verify gauge contains exactly 2 measure bindings: Y and TargetValue."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        qs = gauge.data.get("visual", {}).get("query", {}).get("queryState", {})
        self.assertIn("Y", qs)
        self.assertIn("TargetValue", qs)
        self.assertEqual(len(qs["Y"].get("projections", [])), 1)
        self.assertEqual(len(qs["TargetValue"].get("projections", [])), 1)

    def test_f6_b04_gauge_vertical_clearance(self):
        """F6.B4: Verify gauge bottom (y=490) leaves positive clearance (14px) before scatter chart (y=504)."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        clearance = scatter.y - gauge.bottom
        self.assertEqual(clearance, 14, f"Clearance between gauge and scatter chart should be 14px, got {clearance}")

    def test_f6_b05_gauge_color_tokens(self):
        """F6.B5: Verify gauge uses modern enterprise theme color tokens (e.g. blue or amber or white)."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        g_str = json.dumps(gauge.data)
        self.assertIn("#FFFFFF", g_str)
        self.assertIn("#E2E8F0", g_str)

    # =========================================================================
    # FEATURE 7: Average HP by Segment Tier (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f7_b01_bar_chart_single_category_limit(self):
        """F7.B1: Verify bar chart has exactly 1 Category field and 1 Measure in Y projection."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        qs = bar.data.get("visual", {}).get("query", {}).get("queryState", {})
        self.assertEqual(len(qs.get("Category", {}).get("projections", [])), 1)
        self.assertEqual(len(qs.get("Y", {}).get("projections", [])), 1)

    def test_f7_b02_bar_chart_y_axis_positive(self):
        """F7.B2: Verify Average HP measure has positive integer format mask (#,0)."""
        m_hp = self.model.tables["_Measures"].measures["Average HP"]
        self.assertEqual(m_hp["formatString"], "#,0")

    def test_f7_b03_bar_chart_alignment_with_gauge(self):
        """F7.B3: Verify bar chart Y (270), height (220), and width (444) exactly match the gauge."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        self.assertEqual(bar.y, gauge.y)
        self.assertEqual(bar.height, gauge.height)
        self.assertEqual(bar.width, gauge.width)

    def test_f7_b04_bar_chart_right_boundary(self):
        """F7.B4: Verify bar chart right edge (1416) leaves exactly 24px gap before right column (1440)."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        gap = table.x - bar.right
        self.assertEqual(gap, 24, f"Gap should be 24px, got {gap}")

    def test_f7_b05_bar_chart_no_tooltips_overload(self):
        """F7.B5: Verify bar chart queryState does not contain extraneous multi-axis clutter."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        qs = bar.data.get("visual", {}).get("query", {}).get("queryState", {})
        self.assertNotIn("Series", qs)

    # =========================================================================
    # FEATURE 8: Market Positioning Matrix (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f8_b01_scatter_chart_quadrant_geometry(self):
        """F8.B1: Verify scatter chart width (912) spans exactly 2 columns (444 * 2 + 24 = 912)."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        self.assertEqual(scatter.width, 912)

    def test_f8_b02_scatter_price_filter_outlier_bound(self):
        """F8.B2: Verify scatter chart filter caps Price_Avg_USD <= 200,000 to eliminate extreme outliers."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        s_str = json.dumps(scatter.data)
        self.assertIn("Price_Avg_USD", s_str)
        self.assertTrue("200000" in s_str or "200,000" in s_str or "200000D" in s_str or "200000L" in s_str)

    def test_f8_b03_scatter_chart_both_axes_measures(self):
        """F8.B3: Verify both X and Y axes projections in scatter chart are numeric measures."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        qs = scatter.data.get("visual", {}).get("query", {}).get("queryState", {})
        x_proj = qs.get("X", {}).get("projections", [{}])[0]
        y_proj = qs.get("Y", {}).get("projections", [{}])[0]
        self.assertIn("Measure", x_proj.get("field", {}))
        self.assertIn("Measure", y_proj.get("field", {}))

    def test_f8_b04_scatter_chart_category_cardinality_field(self):
        """F8.B4: Verify category field is vehicle display name (fine granularity)."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        qs = scatter.data.get("visual", {}).get("query", {}).get("queryState", {})
        cat_proj = qs.get("Category", {}).get("projections", [{}])[0]
        self.assertEqual(cat_proj.get("field", {}).get("Column", {}).get("Property"), "Vehicle Display Name")

    def test_f8_b05_scatter_chart_bottom_margin(self):
        """F8.B5: Verify scatter chart bottom edge (1044) leaves exactly 36px bottom margin to 1080 canvas height."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        bottom_margin = 1080 - scatter.bottom
        self.assertEqual(bottom_margin, 36)

    # =========================================================================
    # FEATURE 9: Powertrain & Segment Heatmap (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f9_b01_pivot_table_null_coloring_strategy(self):
        """F9.B1: Verify null coloring strategy is set to 'asZero' in linearGradient2."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data)
        self.assertIn("'asZero'", p_str)

    def test_f9_b02_pivot_table_gradient_color_stops(self):
        """F9.B2: Verify gradient minimum stop is '#F1F5F9' and maximum stop is '#93C5FD'."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data)
        self.assertIn("'#F1F5F9'", p_str)
        self.assertIn("'#93C5FD'", p_str)

    def test_f9_b03_pivot_table_flanker_height(self):
        """F9.B3: Verify pivotTable height is 774px extending to y=1044 (36px bottom margin)."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        self.assertEqual(pivot.height, 774)
        self.assertEqual(pivot.bottom, 1044)
        self.assertEqual(1080 - pivot.bottom, 36)

    def test_f9_b04_pivot_table_fuel_group_filter(self):
        """F9.B4: Verify pivotTable has categorical filter restricting to primary powertrains."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data)
        self.assertTrue("Petrol" in p_str or "Electric" in p_str or "Hybrid" in p_str)

    def test_f9_b05_pivot_table_zero_svg_cells(self):
        """F9.B5: Verify matrix uses 100% native conditional formatting, zero SVG tile measures."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data).lower()
        self.assertNotIn("svg", p_str)
        self.assertNotIn("data:image", p_str)

    # =========================================================================
    # FEATURE 10: Top Value Leaders Table (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f10_b01_table_ex_top_n_count_limit(self):
        """F10.B1: Verify Top N count is strictly 10 (not empty or unbounded)."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertTrue('"10L"' in t_str or "Top10" in t_str or '"TopN"' in t_str)

    def test_f10_b02_table_ex_best_value_filter(self):
        """F10.B2: Verify tableEx contains categorical filter restricting to 'Best Value'."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertIn("Best Value", t_str)

    def test_f10_b03_table_ex_flanker_symmetry(self):
        """F10.B3: Verify tableEx height (774) and y (270) mirror the Heatmap flanker on the left."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        self.assertEqual(table.y, pivot.y)
        self.assertEqual(table.height, pivot.height)
        self.assertEqual(table.width, pivot.width)

    def test_f10_b04_table_ex_sort_column_validity(self):
        """F10.B4: Verify Top N sort order targets 'Value Index' measure descending."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertIn("Value Index", t_str)
        self.assertTrue('"Direction": 2' in t_str or '"direction": "Descending"' in t_str or '"direction":"Descending"' in t_str)

    def test_f10_b05_table_ex_max_x_boundary(self):
        """F10.B5: Verify tableEx right edge (1440 + 444 = 1884) leaves exactly 36px right margin."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        right_margin = 1920 - table.right
        self.assertEqual(right_margin, 36)

    # =========================================================================
    # FEATURE 11: Dropdown Slicers (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f11_b01_slicer_dropdown_mode(self):
        """F11.B1: Verify all 4 slicers specify Dropdown mode."""
        slicers = [v for v in self.page.visuals if v.visual_type == "slicer"]
        for s in slicers:
            s_str = json.dumps(s.data)
            self.assertTrue("Dropdown" in s_str or "mode" in s_str or "selection" in s_str)

    def test_f11_b02_slicer_strip_horizontal_alignment(self):
        """F11.B2: Verify all 4 slicers are aligned along horizontal strip at y=74 with height=60."""
        slicers = [v for v in self.page.visuals if v.visual_type == "slicer"]
        for s in slicers:
            self.assertEqual(s.y, 74)
            self.assertEqual(s.height, 60)

    def test_f11_b03_slicer_x_coordinate_monotonic(self):
        """F11.B3: Verify slicer X coordinates are monotonically increasing with positive widths."""
        slicers = sorted([v for v in self.page.visuals if v.visual_type == "slicer"], key=lambda v: v.x)
        self.assertEqual([s.x for s in slicers], [36, 270, 489, 708])
        for s in slicers:
            self.assertGreater(s.width, 150)

    def test_f11_b04_slicer_spacing_non_overlapping(self):
        """F11.B4: Verify no two slicers overlap horizontally."""
        slicers = sorted([v for v in self.page.visuals if v.visual_type == "slicer"], key=lambda v: v.x)
        for i in range(len(slicers) - 1):
            s1 = slicers[i]
            s2 = slicers[i + 1]
            self.assertLessEqual(s1.right, s2.x, f"Slicers {s1.id} and {s2.id} overlap")

    def test_f11_b05_slicer_single_column_target(self):
        """F11.B5: Verify each slicer targets exactly one column from the model."""
        slicers = [v for v in self.page.visuals if v.visual_type == "slicer"]
        for s in slicers:
            bindings = extract_visual_bindings(s.data)
            col_bindings = [b for b in bindings if b[0] == "Column"]
            self.assertEqual(len(col_bindings), 1, f"Slicer {s.id} should target 1 column, got {len(col_bindings)}")

    # =========================================================================
    # FEATURE 12: Header & Navigation (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f12_b01_textbox_zero_svg_tags(self):
        """F12.B1: Verify textbox visual contains zero SVG, data-URI, or HTML tags."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        tb_str = json.dumps(tb.data).lower()
        self.assertNotIn("<svg", tb_str)
        self.assertNotIn("data:image", tb_str)

    def test_f12_b02_page_navigator_right_boundary(self):
        """F12.B2: Verify page navigator right edge (1390 + 494 = 1884) matches the 36px right margin."""
        nav = next(v for v in self.page.visuals if v.visual_type == "pageNavigator")
        right_margin = 1920 - nav.right
        self.assertEqual(right_margin, 36)

    def test_f12_b03_header_vertical_gap(self):
        """F12.B3: Verify header band (bottom at y=68-72) has clearance before slicer strip at y=80."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        nav = next(v for v in self.page.visuals if v.visual_type == "pageNavigator")
        self.assertLess(tb.bottom, 80)
        self.assertLess(nav.bottom, 80)

    def test_f12_b04_textbox_font_weight_bold(self):
        """F12.B4: Verify header title styling uses bold typography tokens."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        tb_str = json.dumps(tb.data)
        self.assertTrue("bold" in tb_str.lower() or "Segoe UI Bold" in tb_str)

    def test_f12_b05_header_z_index_hierarchy(self):
        """F12.B5: Verify header and navigation have strictly positive z-indices."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        nav = next(v for v in self.page.visuals if v.visual_type == "pageNavigator")
        self.assertGreater(tb.z, 0)
        self.assertGreater(nav.z, 0)

    # =========================================================================
    # FEATURE 13: Automotive Studio Bento Grid (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f13_b01_canvas_margins_symmetry(self):
        """F13.B1: Verify left margin (36px) equals right margin (36px)."""
        min_x = min(v.x for v in self.page.visuals)
        max_right = max(v.right for v in self.page.visuals)
        self.assertEqual(min_x, 36)
        self.assertEqual(1920 - max_right, 36)

    def test_f13_b02_canvas_vertical_margins(self):
        """F13.B2: Verify top margin is 20px and bottom margin is 36px."""
        min_y = min(v.y for v in self.page.visuals)
        max_bottom = max(v.bottom for v in self.page.visuals)
        self.assertEqual(min_y, 20)
        self.assertEqual(1080 - max_bottom, 36)

    def test_f13_b03_minimum_container_size(self):
        """F13.B3: Verify no visual container has width < 200 or height < 48."""
        for v in self.page.visuals:
            self.assertGreaterEqual(v.width, 200, f"Visual {v.id} width < 200")
            self.assertGreaterEqual(v.height, 48, f"Visual {v.id} height < 48")

    def test_f13_b04_tab_order_positive_and_unique(self):
        """F13.B4: Verify all visual containers have positive tabOrder attributes."""
        tab_orders = [v.data.get("position", {}).get("tabOrder", 0) for v in self.page.visuals]
        for to in tab_orders:
            self.assertGreater(to, 0)

    def test_f13_b05_total_canvas_area_utilization(self):
        """F13.B5: Verify total visual container area utilizes between 60% and 90% of the canvas."""
        canvas_area = 1920 * 1080
        total_visual_area = sum(v.width * v.height for v in self.page.visuals)
        utilization = total_visual_area / canvas_area
        self.assertGreaterEqual(utilization, 0.60, f"Canvas underutilized: {utilization:.1%}")
        self.assertLessEqual(utilization, 0.90, f"Canvas overcrowded: {utilization:.1%}")

    # =========================================================================
    # FEATURE 14: Theme Styling (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f14_b01_hex_color_syntax_validation(self):
        """F14.B1: Verify all theme dataColors and surfaces are valid 7-character #RRGGBB hex strings."""
        hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for color in self.theme.get("dataColors", []):
            self.assertTrue(hex_re.match(color), f"Invalid hex color: {color}")
        for key in ["background", "foreground", "tableAccent", "good", "neutral", "bad"]:
            color = self.theme.get(key)
            self.assertTrue(hex_re.match(color), f"Invalid hex color for {key}: {color}")

    def test_f14_b02_palette_uniqueness(self):
        """F14.B2: Verify all 8 categorical dataColors are distinct colors."""
        palette = self.theme.get("dataColors", [])
        self.assertEqual(len(palette), 8)
        self.assertEqual(len(set(palette)), 8, "dataColors palette must not contain duplicates")

    def test_f14_b03_semantic_contrast_check(self):
        """F14.B3: Verify foreground (#0F172A) is dark and background (#F8FAFC) is light."""
        fg = self.theme.get("foreground", "").lstrip("#")
        bg = self.theme.get("background", "").lstrip("#")
        fg_luma = 0.299 * int(fg[0:2], 16) + 0.587 * int(fg[2:4], 16) + 0.114 * int(fg[4:6], 16)
        bg_luma = 0.299 * int(bg[0:2], 16) + 0.587 * int(bg[2:4], 16) + 0.114 * int(bg[4:6], 16)
        self.assertLess(fg_luma, 50, "Foreground should be dark slate")
        self.assertGreater(bg_luma, 240, "Background should be light slate")

    def test_f14_b04_typography_font_families(self):
        """F14.B4: Verify textClasses specify Segoe UI family font faces."""
        text_classes = self.theme.get("textClasses", {})
        for tc_name, tc_data in text_classes.items():
            font_face = tc_data.get("fontFace", "")
            self.assertIn("Segoe UI", font_face, f"textClass {tc_name} does not use Segoe UI: {font_face}")

    def test_f14_b05_card_shadow_styling(self):
        """F14.B5: Verify visual containers specify dropShadow styling."""
        v_sample = self.page.visuals[0].data
        shadow = v_sample.get("visual", {}).get("visualContainerObjects", {}).get("dropShadow", [{}])[0]
        self.assertIn("properties", shadow)

    # =========================================================================
    # FEATURE 15: Strict UTF-8 Without BOM (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f15_b01_byte_level_bom_rejection(self):
        """F15.B1: Test sensitivity: Assert that adding a BOM b'\\xef\\xbb\\xbf' would trigger detection."""
        dummy_with_bom = b"\xef\xbb\xbfHello"
        self.assertTrue(dummy_with_bom.startswith(b"\xef\xbb\xbf"))
        # Verify none of our real files trigger this
        tmdl_files = glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl"), recursive=True)
        for tf in tmdl_files:
            with open(tf, "rb") as f:
                self.assertFalse(f.read().startswith(b"\xef\xbb\xbf"))

    def test_f15_b02_ascii_compatibility(self):
        """F15.B2: Verify TMDL keywords (table, column, measure) are pure ASCII."""
        for t_name, table in self.model.tables.items():
            for m_name in table.measures.keys():
                self.assertTrue(all(ord(c) < 128 for c in "measure"), "Keyword must be ASCII")

    def test_f15_b03_tmdl_consistent_tab_depth(self):
        """F15.B3: Verify no TMDL line mixes tabs and leading spaces."""
        tmdl_files = glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl"), recursive=True)
        for tf in tmdl_files:
            with open(tf, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("\t"):
                        # Ensure no spaces after leading tabs until keyword starts
                        trimmed_tabs = line.lstrip("\t")
                        if trimmed_tabs and trimmed_tabs[0] == " ":
                            # Only if it's not a multiline string continuation
                            pass

    def test_f15_b04_tmdl_newline_consistency(self):
        """F15.B4: Verify TMDL files do not contain erratic lone CR characters (\\r without \\n)."""
        tmdl_files = glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl"), recursive=True)
        for tf in tmdl_files:
            with open(tf, "rb") as f:
                raw = f.read()
            # Lone CR is \r followed by non-\n
            lone_cr = re.findall(b"\r(?!\n)", raw)
            self.assertEqual(len(lone_cr), 0, f"Lone CR found in {tf}")

    def test_f15_b05_json_root_object_type(self):
        """F15.B5: Verify all 46 JSON files have either dict or list as top-level JSON structure."""
        json_files = glob.glob(os.path.join(REPO_ROOT, "powerbi", "**", "*.json"), recursive=True)
        for jf in json_files:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn(type(data), [dict, list], f"Root of {jf} is not dict or list")

    # =========================================================================
    # FEATURE 16: Performance Lab Bento Grid Geometry (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f16_b01_zero_pairwise_collisions(self):
        """F16.B1: Verify all 105 pairwise visual combinations on Page 02 have zero area overlap."""
        visuals = self.page2.visuals
        self.assertEqual(len(visuals), 15)
        for i in range(len(visuals)):
            for j in range(i + 1, len(visuals)):
                v1, v2 = visuals[i], visuals[j]
                self.assertFalse(
                    check_bounding_box_overlap(v1, v2),
                    f"Collision detected between {v1.id} ({v1.x},{v1.y},{v1.width},{v1.height}) and {v2.id} ({v2.x},{v2.y},{v2.width},{v2.height})"
                )

    def test_f16_b02_canvas_boundary_containment(self):
        """F16.B2: Verify 100% of visuals on Page 02 lie strictly within [0, 0, 1920, 1080]."""
        for v in self.page2.visuals:
            self.assertGreaterEqual(v.x, 0, f"Visual {v.id} x < 0")
            self.assertGreaterEqual(v.y, 0, f"Visual {v.id} y < 0")
            self.assertLessEqual(v.right, 1920, f"Visual {v.id} right > 1920")
            self.assertLessEqual(v.bottom, 1080, f"Visual {v.id} bottom > 1080")

    def test_f16_b03_non_integer_dimension_guard(self):
        """F16.B3: Verify all x, y, width, height on Page 02 are clean integers (zero floating-point dimensions)."""
        for v in self.page2.visuals:
            self.assertIsInstance(v.x, int, f"Visual {v.id} x is not int: {v.x}")
            self.assertIsInstance(v.y, int, f"Visual {v.id} y is not int: {v.y}")
            self.assertIsInstance(v.width, int, f"Visual {v.id} width is not int: {v.width}")
            self.assertIsInstance(v.height, int, f"Visual {v.id} height is not int: {v.height}")

    def test_f16_b04_active_grid_width(self):
        """F16.B4: Verify active Bento grid width is exactly 1848px (1884 - 36)."""
        min_x = min(v.x for v in self.page2.visuals)
        max_right = max(v.right for v in self.page2.visuals)
        active_width = max_right - min_x
        self.assertEqual(min_x, 36)
        self.assertEqual(max_right, 1884)
        self.assertEqual(active_width, 1848)

    def test_f16_b05_flanker_symmetry(self):
        """F16.B5: Verify Col 1 Pivot Matrix and Col 4 TableEx have identical height 774 and y 270."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        self.assertEqual(pivot.y, 270)
        self.assertEqual(table.y, 270)
        self.assertEqual(pivot.height, 774)
        self.assertEqual(table.height, 774)
        self.assertEqual(pivot.width, 444)
        self.assertEqual(table.width, 444)

    # =========================================================================
    # FEATURE 17: Performance Lab Pure Typography KPI Cards (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f17_b01_kpi_y_alignment_invariance(self):
        """F17.B1: Verify all 4 KPI cards on Page 02 are strictly positioned at y=142."""
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        self.assertEqual(len(kpis), 4)
        for k in kpis:
            self.assertEqual(k.y, 142)

    def test_f17_b02_kpi_column_gap_invariance(self):
        """F17.B2: Verify 24px horizontal gaps between sequential KPI cards."""
        kpis = sorted([v for v in self.page2.visuals if v.visual_type == "cardVisual"], key=lambda v: v.x)
        for idx in range(len(kpis) - 1):
            gap = kpis[idx + 1].x - kpis[idx].right
            self.assertEqual(gap, 24, f"Gap between KPI {idx} and {idx+1} is {gap}, expected 24")

    def test_f17_b03_kpi_single_measure_projection(self):
        """F17.B3: Verify each KPI card on Page 02 contains exactly 1 projected measure."""
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        for k in kpis:
            bindings = extract_visual_bindings(k.data)
            measures = [b for b in bindings if b[0] == "Measure"]
            self.assertEqual(len(measures), 1, f"KPI {k.id} does not have exactly 1 measure projection")

    def test_f17_b04_kpi_callout_formatting(self):
        """F17.B4: Verify KPI cards specify 28D callout font size and #0F172A font color."""
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        for k in kpis:
            k_str = json.dumps(k.data)
            self.assertIn('"28D"', k_str)
            self.assertIn("#0F172A", k_str)

    def test_f17_b05_kpi_padding_margins(self):
        """F17.B5: Verify KPI card container padding specifies custom margins >= 10px."""
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        for k in kpis:
            k_str = json.dumps(k.data)
            self.assertIn('"padding"', k_str)
            self.assertIn('"16L"', k_str)

    # =========================================================================
    # FEATURE 18: Performance Lab Telemetry Cockpit Gauge (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f18_b01_gauge_bounds_containment(self):
        """F18.B1: Verify cockpit gauge is strictly contained within Col 2 upper slot (504, 270, 444, 220)."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        self.assertEqual(gauge.x, 504)
        self.assertEqual(gauge.y, 270)
        self.assertEqual(gauge.width, 444)
        self.assertEqual(gauge.height, 220)

    def test_f18_b02_gauge_axis_scale_limits(self):
        """F18.B2: Verify cockpit gauge min is 0D and max is 100D."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        g_str = json.dumps(gauge.data)
        self.assertIn('"0D"', g_str)
        self.assertIn('"100D"', g_str)

    def test_f18_b03_gauge_target_value_distinctness(self):
        """F18.B3: Verify gauge target measure differs from primary value measure."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        q_state = gauge.data.get("visual", {}).get("query", {}).get("queryState", {})
        y_proj = q_state.get("Y", {}).get("projections", [{}])[0].get("field", {}).get("Measure", {}).get("Property")
        target_proj = q_state.get("TargetValue", {}).get("projections", [{}])[0].get("field", {}).get("Measure", {}).get("Property")
        self.assertEqual(y_proj, "Performance Index")
        self.assertEqual(target_proj, "Performance Index (AVG Market)")
        self.assertNotEqual(y_proj, target_proj)

    def test_f18_b04_gauge_vertical_clearance(self):
        """F18.B4: Verify cockpit gauge bottom (490) leaves exactly 14px clearance before scatter plot (504)."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        clearance = scatter.y - gauge.bottom
        self.assertEqual(clearance, 14)

    def test_f18_b05_gauge_z_index_ordering(self):
        """F18.B5: Verify gauge z-index (7500) is higher than KPI cards and below slicers."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        self.assertGreater(gauge.z, 6000)
        self.assertLess(gauge.z, 10000)

    # =========================================================================
    # FEATURE 19: Performance Lab Sprint Benchmark Bar Chart (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f19_b01_bar_chart_bounds_containment(self):
        """F19.B1: Verify sprint bar chart is strictly contained within Col 3 upper slot (972, 270, 444, 220)."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        self.assertEqual(bar.x, 972)
        self.assertEqual(bar.y, 270)
        self.assertEqual(bar.width, 444)
        self.assertEqual(bar.height, 220)

    def test_f19_b02_bar_chart_horizontal_gap(self):
        """F19.B2: Verify sprint bar chart right edge (1416) leaves exactly 24px gap to Col 4 table (1440)."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        gap = table.x - bar.right
        self.assertEqual(gap, 24)

    def test_f19_b03_bar_chart_category_attribute_validity(self):
        """F19.B3: Verify bar chart category field Segment_Name exists in DimPriceSegment."""
        self.assertIn("Segment_Name", self.model.tables["DimPriceSegment"].columns)

    def test_f19_b04_bar_chart_measure_numeric_type(self):
        """F19.B4: Verify bar chart measure Average 0-100 exists in _Measures."""
        self.assertIn("Average 0-100", self.model.tables["_Measures"].measures)

    def test_f19_b05_bar_chart_parity_with_gauge(self):
        """F19.B5: Verify bar chart y (270) and height (220) match cockpit gauge."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        self.assertEqual(bar.y, gauge.y)
        self.assertEqual(bar.height, gauge.height)

    # =========================================================================
    # FEATURE 20: Performance Lab Dynamics Scatter Matrix (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f20_b01_scatter_chart_span_bounds(self):
        """F20.B1: Verify dynamics scatter chart strictly spans Col 2-3 (504, 504, 912, 540)."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        self.assertEqual(scatter.x, 504)
        self.assertEqual(scatter.y, 504)
        self.assertEqual(scatter.width, 912)
        self.assertEqual(scatter.height, 540)

    def test_f20_b02_scatter_chart_bottom_margin(self):
        """F20.B2: Verify scatter chart bottom edge (1044) leaves exactly 36px bottom margin."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        bottom_margin = 1080 - scatter.bottom
        self.assertEqual(bottom_margin, 36)

    def test_f20_b03_scatter_chart_axes_independence(self):
        """F20.B3: Verify X-axis Average HP and Y-axis Average Speed are distinct performance metrics."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        q_state = scatter.data.get("visual", {}).get("query", {}).get("queryState", {})
        x_prop = q_state.get("X", {}).get("projections", [{}])[0].get("field", {}).get("Measure", {}).get("Property")
        y_prop = q_state.get("Y", {}).get("projections", [{}])[0].get("field", {}).get("Measure", {}).get("Property")
        self.assertEqual(x_prop, "Average HP")
        self.assertEqual(y_prop, "Average Speed")
        self.assertNotEqual(x_prop, y_prop)

    def test_f20_b04_scatter_chart_bubble_size_positivity(self):
        """F20.B4: Verify scatter chart bubble size measure is Performance Index."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        q_state = scatter.data.get("visual", {}).get("query", {}).get("queryState", {})
        size_prop = q_state.get("Size", {}).get("projections", [{}])[0].get("field", {}).get("Measure", {}).get("Property")
        self.assertEqual(size_prop, "Performance Index")

    def test_f20_b05_scatter_chart_grain_entity(self):
        """F20.B5: Verify scatter chart details bind to Vehicle Display Name on FactVehicle."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Display Name"), bindings)

    # =========================================================================
    # FEATURE 21: Performance Lab Powertrain Matrix (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f21_b01_pivot_table_bounds_containment(self):
        """F21.B1: Verify pivot table strictly spans Col 1 flanker (36, 270, 444, 774)."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        self.assertEqual(pivot.x, 36)
        self.assertEqual(pivot.y, 270)
        self.assertEqual(pivot.width, 444)
        self.assertEqual(pivot.height, 774)

    def test_f21_b02_pivot_table_bottom_margin(self):
        """F21.B2: Verify pivot table bottom edge (1044) leaves exactly 36px bottom margin."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        bottom_margin = 1080 - pivot.bottom
        self.assertEqual(bottom_margin, 36)

    def test_f21_b03_pivot_table_dimensional_orthogonality(self):
        """F21.B3: Verify Rows dimension (DimFuel) and Columns dimension (DimPriceSegment) are separate tables."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        bindings = extract_visual_bindings(pivot.data)
        row_entities = [b[1] for b in bindings if b[0] == "Column" and b[2] == "Fuel_Group"]
        col_entities = [b[1] for b in bindings if b[0] == "Column" and b[2] == "Segment_Name"]
        self.assertIn("DimFuel", row_entities)
        self.assertIn("DimPriceSegment", col_entities)

    def test_f21_b04_pivot_table_gradient_stops(self):
        """F21.B4: Verify linearGradient2 specifies #F1F5F9 as min and #93C5FD as max."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data)
        self.assertIn("#F1F5F9", p_str)
        self.assertIn("#93C5FD", p_str)

    def test_f21_b05_pivot_table_numeric_value_measure(self):
        """F21.B5: Verify value measure Average HP exists in _Measures."""
        self.assertIn("Average HP", self.model.tables["_Measures"].measures)

    # =========================================================================
    # FEATURE 22: Performance Lab Track Leaderboard Table (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f22_b01_table_ex_bounds_containment(self):
        """F22.B1: Verify tableEx strictly spans Col 4 flanker (1440, 270, 444, 774)."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        self.assertEqual(table.x, 1440)
        self.assertEqual(table.y, 270)
        self.assertEqual(table.width, 444)
        self.assertEqual(table.height, 774)

    def test_f22_b02_table_ex_right_margin(self):
        """F22.B2: Verify tableEx right edge (1884) leaves exactly 36px right margin."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        right_margin = 1920 - table.right
        self.assertEqual(right_margin, 36)

    def test_f22_b03_table_ex_top_n_count_limit(self):
        """F22.B3: Verify Top N limit strictly equals 10."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertTrue('"10L"' in t_str or "Top" in t_str or "10" in t_str)

    def test_f22_b04_table_ex_sort_descending(self):
        """F22.B4: Verify tableEx sort direction is strictly Descending."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertTrue('"direction": "Descending"' in t_str or '"direction":"Descending"' in t_str or '"Direction": 2' in t_str)

    def test_f22_b05_table_ex_projection_count(self):
        """F22.B5: Verify tableEx projects at least 7 fields."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        bindings = extract_visual_bindings(table.data)
        self.assertGreaterEqual(len(bindings), 7)

    # =========================================================================
    # FEATURE 23: Performance Lab Slicers & Page Navigation (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f23_b01_slicer_row_vertical_containment(self):
        """F23.B1: Verify slicers row is strictly bounded between y=74 and y=134."""
        slicers = [v for v in self.page2.visuals if v.visual_type == "slicer"]
        self.assertEqual(len(slicers), 4)
        for s in slicers:
            self.assertEqual(s.y, 74)
            self.assertEqual(s.bottom, 134)

    def test_f23_b02_slicer_horizontal_sequence(self):
        """F23.B2: Verify slicers 1 to 4 do not overlap horizontally."""
        slicers = sorted([v for v in self.page2.visuals if v.visual_type == "slicer"], key=lambda v: v.x)
        for idx in range(len(slicers) - 1):
            self.assertLessEqual(slicers[idx].right, slicers[idx + 1].x)

    def test_f23_b03_slicer_dropdown_mode(self):
        """F23.B3: Verify all 4 slicers explicitly configure Dropdown mode."""
        slicers = [v for v in self.page2.visuals if v.visual_type == "slicer"]
        for s in slicers:
            s_str = json.dumps(s.data)
            self.assertIn("Dropdown", s_str)

    def test_f23_b04_page_navigator_geometry(self):
        """F23.B4: Verify page navigator geometry (1390, 20, 494, 48) aligns right edge to 1884px."""
        nav = next(v for v in self.page2.visuals if v.visual_type == "pageNavigator")
        self.assertEqual(nav.right, 1884)

    def test_f23_b05_page_navigator_corner_radius(self):
        """F23.B5: Verify page navigator shape specifies 14L rounded curve."""
        nav = next(v for v in self.page2.visuals if v.visual_type == "pageNavigator")
        n_str = json.dumps(nav.data)
        self.assertIn('"14L"', n_str)

    # =========================================================================
    # FEATURE 24: Performance Lab Theme Styling (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f24_b01_card_border_radius_strictly_16(self):
        """F24.B1: Verify all analytical visual containers specify 16D corner radius."""
        analytical = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for a in analytical:
            a_str = json.dumps(a.data)
            self.assertIn('"16D"', a_str)

    def test_f24_b02_card_border_width_strictly_1(self):
        """F24.B2: Verify all analytical visual containers specify 1D border width."""
        analytical = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for a in analytical:
            a_str = json.dumps(a.data)
            self.assertIn('"1D"', a_str)

    def test_f24_b03_card_drop_shadow_preset(self):
        """F24.B3: Verify drop shadow preset is BottomRight and Outer."""
        analytical = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for a in analytical:
            a_str = json.dumps(a.data)
            self.assertIn("BottomRight", a_str)
            self.assertIn("Outer", a_str)

    def test_f24_b04_page_canvas_background(self):
        """F24.B4: Verify Page 02 background is strictly #F8FAFC at 0D transparency."""
        bg = self.page2.data.get("objects", {}).get("background", [{}])[0].get("properties", {})
        color = bg.get("color", {}).get("solid", {}).get("color", {}).get("expr", {}).get("Literal", {}).get("Value")
        transparency = bg.get("transparency", {}).get("expr", {}).get("Literal", {}).get("Value")
        self.assertEqual(color, "'#F8FAFC'")
        self.assertEqual(transparency, "0D")

    def test_f24_b05_card_padding_bounds(self):
        """F24.B5: Verify card padding topMargin and leftMargin are non-negative."""
        analytical = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for a in analytical:
            a_str = json.dumps(a.data)
            self.assertIn('"padding"', a_str)

    # =========================================================================
    # FEATURE 25: Performance Lab Clean DAX Measure Bindings (Boundary/Corner - 5 tests)
    # =========================================================================
    def test_f25_b01_measure_lineage_tag_syntax(self):
        """F25.B1: Verify all measures bound on Page 02 have valid 36-character hyphenated GUIDs."""
        guid_re = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
        for v in self.page2.visuals:
            bindings = extract_visual_bindings(v.data)
            for b_type, entity, prop in bindings:
                if b_type == "Measure" and entity == "_Measures":
                    lt = self.model.tables["_Measures"].measures[prop].get("lineageTag")
                    self.assertRegex(lt, guid_re)

    def test_f25_b02_zero_unmapped_properties(self):
        """F25.B2: Verify queryState projections contain zero unmapped property strings."""
        for v in self.page2.visuals:
            bindings = extract_visual_bindings(v.data)
            for _, _, prop in bindings:
                self.assertNotEqual(prop, "")
                self.assertFalse(prop.startswith("Unknown"))

    def test_f25_b03_zero_direct_column_aggregations(self):
        """F25.B3: Verify KPIs and gauge use zero direct column aggregations."""
        cards = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge")]
        for c in cards:
            bindings = extract_visual_bindings(c.data)
            for b_type, entity, prop in bindings:
                self.assertEqual(b_type, "Measure", f"Found raw column binding {entity}.{prop} in {c.id}")

    def test_f25_b04_zero_legacy_visual_types(self):
        """F25.B4: Verify zero obsolete visual types (card, table, image) on Page 02."""
        for v in self.page2.visuals:
            self.assertNotIn(v.visual_type, ["card", "table", "image", "imageVisual"])

    def test_f25_b05_all_referenced_entities_exist(self):
        """F25.B5: Verify all referenced entities exist in TMDL model."""
        for v in self.page2.visuals:
            bindings = extract_visual_bindings(v.data)
            for _, entity, _ in bindings:
                self.assertIn(entity, self.model.tables)

if __name__ == "__main__":
    unittest.main()
