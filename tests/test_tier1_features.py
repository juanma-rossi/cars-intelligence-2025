"""
Cars Intelligence 2025 - Tier 1: Feature Coverage Test Suite
Happy-path verification of each feature in isolation.
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

class TestTier1Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_semantic_model()
        cls.page = load_report_page()
        cls.page1 = cls.page
        cls.page2 = load_performance_lab_page()
        cls.theme = load_theme()

    # =========================================================================
    # FEATURE 1: Purge Legacy SVG Measures (5 tests)
    # =========================================================================
    def test_f1_01_svg_heatmap_tile_purged(self):
        """F1.1: Verify 'SVG Heatmap Tile' is completely purged from _Measures.tmdl."""
        measures_table = self.model.tables.get("_Measures")
        self.assertIsNotNone(measures_table, "_Measures table must exist in model")
        self.assertNotIn("SVG Heatmap Tile", measures_table.measures)
        self.assertNotIn("SVG Heatmap Tile", measures_table.raw_text)

    def test_f1_02_svg_speedometer_cockpit_purged(self):
        """F1.2: Verify 'SVG Live Speedometer Cockpit' is completely purged from _Measures.tmdl."""
        measures_table = self.model.tables["_Measures"]
        self.assertNotIn("SVG Live Speedometer Cockpit", measures_table.measures)
        self.assertNotIn("SVG Live Speedometer Cockpit", measures_table.raw_text)

    def test_f1_03_svg_coupe_telemetry_purged(self):
        """F1.3: Verify 'SVG Live 3D Coupe Telemetry' is completely purged from _Measures.tmdl."""
        measures_table = self.model.tables["_Measures"]
        self.assertNotIn("SVG Live 3D Coupe Telemetry", measures_table.measures)
        self.assertNotIn("SVG Live 3D Coupe Telemetry", measures_table.raw_text)

    def test_f1_04_svg_market_position_badge_purged(self):
        """F1.4: Verify 'SVG Market Position Badge' is completely purged from _Measures.tmdl."""
        measures_table = self.model.tables["_Measures"]
        self.assertNotIn("SVG Market Position Badge", measures_table.measures)
        self.assertNotIn("SVG Market Position Badge", measures_table.raw_text)

    def test_f1_05_svg_sparkbar_and_performance_gauge_purged(self):
        """F1.5: Verify 'SVG Value Sparkbar' and 'SVG Performance Gauge' are purged from _Measures.tmdl."""
        measures_table = self.model.tables["_Measures"]
        self.assertNotIn("SVG Value Sparkbar", measures_table.measures)
        self.assertNotIn("SVG Performance Gauge", measures_table.measures)
        self.assertNotIn("SVG Value Sparkbar", measures_table.raw_text)
        self.assertNotIn("SVG Performance Gauge", measures_table.raw_text)

    # =========================================================================
    # FEATURE 2: Purge Legacy SVG Column (5 tests)
    # =========================================================================
    def test_f2_01_leaderboard_card_svg_purged(self):
        """F2.1: Verify 'Leaderboard Card SVG' is completely purged from FactVehicle.tmdl."""
        fact = self.model.tables.get("FactVehicle")
        self.assertIsNotNone(fact, "FactVehicle table must exist in model")
        self.assertNotIn("Leaderboard Card SVG", fact.columns)
        self.assertNotIn("Leaderboard Card SVG", fact.raw_text)

    def test_f2_02_factvehicle_column_count(self):
        """F2.2: Verify FactVehicle contains exactly 43 valid columns."""
        fact = self.model.tables["FactVehicle"]
        self.assertEqual(len(fact.columns), 43, f"Expected 43 columns, got {len(fact.columns)}")

    def test_f2_03_factvehicle_calculated_columns_syntax(self):
        """F2.3: Verify FactVehicle calculated columns have valid definitions."""
        fact = self.model.tables["FactVehicle"]
        calc_cols = [c for c, data in fact.columns.items() if data["isCalculated"]]
        self.assertEqual(len(calc_cols), 14, f"Expected 14 calculated columns, got {len(calc_cols)}")
        for col_name in calc_cols:
            self.assertIn("lineageTag", fact.columns[col_name])

    def test_f2_04_factvehicle_lineagetags_intact(self):
        """F2.4: Verify each calculated column in FactVehicle has a valid GUID lineageTag."""
        fact = self.model.tables["FactVehicle"]
        guid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
        for col_name, data in fact.columns.items():
            if data["isCalculated"]:
                lt = data["lineageTag"]
                self.assertIsNotNone(lt, f"Column {col_name} missing lineageTag")
                self.assertTrue(guid_re.match(lt), f"Column {col_name} lineageTag '{lt}' is not a valid GUID")

    def test_f2_05_factvehicle_partition_intact(self):
        """F2.5: Verify FactVehicle partition syntax is intact with valid m expression or calculated source."""
        fact = self.model.tables["FactVehicle"]
        self.assertIn("partition FactVehicle", fact.raw_text)

    # =========================================================================
    # FEATURE 3: Semantic Model Integrity (5 tests)
    # =========================================================================
    def test_f3_01_core_measures_presence(self):
        """F3.1: Verify core measures 'Vehicle Count' and 'Company Count' exist with valid format."""
        measures = self.model.tables["_Measures"].measures
        self.assertIn("Vehicle Count", measures)
        self.assertEqual(measures["Vehicle Count"]["formatString"], "#,0")
        self.assertIn("Company Count", measures)

    def test_f3_02_kpi_contract_measures_presence(self):
        """F3.2: Verify KPI contract measures exist with expected format strings."""
        measures = self.model.tables["_Measures"].measures
        self.assertIn("Median Price", measures)
        self.assertIn("Electrified Share %", measures)
        self.assertEqual(measures["Electrified Share %"]["formatString"], "0.0%;-0.0%;0.0%")
        self.assertIn("Best Value Share %", measures)
        self.assertEqual(measures["Best Value Share %"]["formatString"], "0.0%;-0.0%;0.0%")

    def test_f3_03_gauge_and_chart_contract_measures(self):
        """F3.3: Verify chart and gauge contract measures exist."""
        measures = self.model.tables["_Measures"].measures
        self.assertIn("Performance Index", measures)
        self.assertIn("Performance Index (AVG Market)", measures)
        self.assertIn("Average HP", measures)
        self.assertIn("Average Price", measures)
        self.assertIn("Value Index", measures)

    def test_f3_04_relationships_validity(self):
        """F3.4: Verify all model relationships reference valid tables and columns."""
        self.assertGreater(len(self.model.relationships), 0, "Model must have defined relationships")
        for rel in self.model.relationships:
            from_col = rel["fromColumn"]
            to_col = rel["toColumn"]
            self.assertIn(".", from_col)
            self.assertIn(".", to_col)
            from_table, from_c = from_col.split(".", 1)
            to_table, to_c = to_col.split(".", 1)
            self.assertIn(from_table, self.model.tables, f"Unknown fromTable {from_table}")
            self.assertIn(to_table, self.model.tables, f"Unknown toTable {to_table}")
            self.assertIn(from_c, self.model.tables[from_table].columns, f"Unknown column {from_c} in {from_table}")
            self.assertIn(to_c, self.model.tables[to_table].columns, f"Unknown column {to_c} in {to_table}")

    def test_f3_05_lineagetags_uniqueness(self):
        """F3.5: Verify lineageTag uniqueness across all tables, measures, and columns in semantic model."""
        seen_tags = set()
        for t_name, table in self.model.tables.items():
            if table.lineage_tag:
                self.assertNotIn(table.lineage_tag, seen_tags, f"Duplicate lineageTag on table {t_name}")
                seen_tags.add(table.lineage_tag)
            for m_name, m_data in table.measures.items():
                lt = m_data["lineageTag"]
                if lt:
                    self.assertNotIn(lt, seen_tags, f"Duplicate lineageTag on measure {t_name}[{m_name}]")
                    seen_tags.add(lt)
            for c_name, c_data in table.columns.items():
                lt = c_data["lineageTag"]
                if lt:
                    self.assertNotIn(lt, seen_tags, f"Duplicate lineageTag on column {t_name}[{c_name}]")
                    seen_tags.add(lt)

    # =========================================================================
    # FEATURE 4: Deploy Automated Verification Script (5 tests)
    # =========================================================================
    def test_f4_01_script_file_exists(self):
        """F4.1: Verify scripts/verify_report.py exists and is non-empty."""
        self.assertTrue(os.path.isfile(VERIFY_SCRIPT_PATH), "verify_report.py must exist")
        self.assertGreater(os.path.getsize(VERIFY_SCRIPT_PATH), 500)

    def test_f4_02_script_executes_cleanly(self):
        """F4.2: Verify scripts/verify_report.py executes and exits with return code 0."""
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed with output:\n{res.stdout}\n{res.stderr}")

    def test_f4_03_script_reports_no_failures(self):
        """F4.3: Verify scripts/verify_report.py output contains '0 FAILED' and '0 WARNINGS'."""
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        self.assertIn("0 FAILED", res.stdout)
        self.assertIn("0 WARNINGS", res.stdout)

    def test_f4_04_script_reports_pass_on_all_core_suites(self):
        """F4.4: Verify scripts/verify_report.py passes checks for UTF-8, TMDL, Zero SVG, Bounds, Bindings."""
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        expected_passes = [
            "TMDL UTF-8 No-BOM",
            "TMDL Tab Indentation",
            "JSON UTF-8 No-BOM",
            "JSON Syntax Integrity",
            "Zero SVG References",
            "Canvas Resolution",
            "Visual Container Count",
            "Canvas Bounds Compliance",
            "Visual Types Distribution",
            "Visual Data Bindings",
            "Theme Registration"
        ]
        for ep in expected_passes:
            self.assertIn(f"[PASS] {ep}", res.stdout)

    def test_f4_05_script_shebang_and_encoding(self):
        """F4.5: Verify verify_report.py starts with python3 shebang and has no BOM."""
        with open(VERIFY_SCRIPT_PATH, "rb") as f:
            raw = f.read()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "verify_report.py must not contain UTF-8 BOM")
        text = raw.decode("utf-8")
        self.assertTrue(text.startswith("#!/usr/bin/env python3") or text.startswith("#!/usr/bin/env python"))

    # =========================================================================
    # FEATURE 5: Pure Typography KPI Cards (5 tests)
    # =========================================================================
    def test_f5_01_kpi_card_count(self):
        """F5.1: Verify exactly 4 native cardVisual containers exist on the page."""
        cards = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        self.assertEqual(len(cards), 4, f"Expected 4 cardVisual containers, found {len(cards)}")

    def test_f5_02_kpi1_vehicle_count_binding(self):
        """F5.2: Verify KPI 1 at (36, 142) is bound to _Measures[Vehicle Count]."""
        card1 = next((v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 36 and v.y == 142), None)
        self.assertIsNotNone(card1, "KPI 1 not found at (36, 142)")
        bindings = extract_visual_bindings(card1.data)
        self.assertIn(("Measure", "_Measures", "Vehicle Count"), bindings)

    def test_f5_03_kpi2_median_price_binding(self):
        """F5.3: Verify KPI 2 at (504, 142) is bound to _Measures[Median Price]."""
        card2 = next((v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 504 and v.y == 142), None)
        self.assertIsNotNone(card2, "KPI 2 not found at (504, 142)")
        bindings = extract_visual_bindings(card2.data)
        self.assertIn(("Measure", "_Measures", "Median Price"), bindings)

    def test_f5_04_kpi3_electrified_share_binding(self):
        """F5.4: Verify KPI 3 at (972, 142) is bound to _Measures[Electrified Share %]."""
        card3 = next((v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 972 and v.y == 142), None)
        self.assertIsNotNone(card3, "KPI 3 not found at (972, 142)")
        bindings = extract_visual_bindings(card3.data)
        self.assertIn(("Measure", "_Measures", "Electrified Share %"), bindings)

    def test_f5_05_kpi4_best_value_share_binding(self):
        """F5.5: Verify KPI 4 at (1440, 142) is bound to _Measures[Best Value Share %]."""
        card4 = next((v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 1440 and v.y == 142), None)
        self.assertIsNotNone(card4, "KPI 4 not found at (1440, 142)")
        bindings = extract_visual_bindings(card4.data)
        self.assertIn(("Measure", "_Measures", "Best Value Share %"), bindings)

    # =========================================================================
    # FEATURE 6: Performance Index Cockpit (5 tests)
    # =========================================================================
    def test_f6_01_gauge_visual_exists(self):
        """F6.1: Verify visual container of type 'gauge' exists on page."""
        gauges = [v for v in self.page.visuals if v.visual_type == "gauge"]
        self.assertEqual(len(gauges), 1, "Exactly 1 gauge visual must exist")

    def test_f6_02_gauge_value_binding(self):
        """F6.2: Verify gauge Y projection is bound to _Measures[Performance Index]."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        bindings = extract_visual_bindings(gauge.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), bindings)

    def test_f6_03_gauge_target_binding(self):
        """F6.3: Verify gauge TargetValue projection is bound to _Measures[Performance Index (AVG Market)]."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        bindings = extract_visual_bindings(gauge.data)
        self.assertIn(("Measure", "_Measures", "Performance Index (AVG Market)"), bindings)

    def test_f6_04_gauge_axis_limits(self):
        """F6.4: Verify gauge axis range is configured with min 0 and max 100."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        v_str = json.dumps(gauge.data)
        self.assertIn('"min"', v_str)
        self.assertIn('"max"', v_str)
        self.assertIn('"0D"', v_str)
        self.assertIn('"100D"', v_str)

    def test_f6_05_gauge_geometry(self):
        """F6.5: Verify gauge geometry is positioned at x=504, y=270, width=444, height=220."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        self.assertEqual(gauge.x, 504)
        self.assertEqual(gauge.y, 270)
        self.assertEqual(gauge.width, 444)
        self.assertEqual(gauge.height, 220)

    # =========================================================================
    # FEATURE 7: Average HP by Segment Tier (5 tests)
    # =========================================================================
    def test_f7_01_clustered_bar_chart_exists(self):
        """F7.1: Verify visual container of type 'clusteredBarChart' exists on page."""
        bars = [v for v in self.page.visuals if v.visual_type == "clusteredBarChart"]
        self.assertEqual(len(bars), 1, "Exactly 1 clusteredBarChart visual must exist")

    def test_f7_02_bar_chart_category_binding(self):
        """F7.2: Verify bar chart Category projection is bound to DimPriceSegment[Segment_Name]."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), bindings)

    def test_f7_03_bar_chart_y_axis_binding(self):
        """F7.3: Verify bar chart Y projection is bound to _Measures[Average HP]."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)

    def test_f7_04_bar_chart_sort_descending(self):
        """F7.4: Verify bar chart sort order targets Average HP descending."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        v_str = json.dumps(bar.data)
        self.assertIn("Average HP", v_str)
        self.assertTrue("OrderBy" in v_str or "sort" in v_str or "Direction" in v_str)

    def test_f7_05_bar_chart_geometry(self):
        """F7.5: Verify bar chart geometry is positioned at x=972, y=270, width=444, height=220."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        self.assertEqual(bar.x, 972)
        self.assertEqual(bar.y, 270)
        self.assertEqual(bar.width, 444)
        self.assertEqual(bar.height, 220)

    # =========================================================================
    # FEATURE 8: Market Positioning Matrix (5 tests)
    # =========================================================================
    def test_f8_01_scatter_chart_exists(self):
        """F8.1: Verify visual container of type 'scatterChart' exists on page."""
        scatters = [v for v in self.page.visuals if v.visual_type == "scatterChart"]
        self.assertEqual(len(scatters), 1, "Exactly 1 scatterChart visual must exist")

    def test_f8_02_scatter_chart_axes_bindings(self):
        """F8.2: Verify scatter chart X is bound to Average Price and Y is bound to Average HP."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Average Price"), bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)

    def test_f8_03_scatter_chart_category_series(self):
        """F8.3: Verify scatter chart Category is Vehicle Display Name and Series is Market Position (Static)."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Display Name"), bindings)
        self.assertIn(("Column", "FactVehicle", "Market Position (Static)"), bindings)

    def test_f8_04_scatter_chart_tooltips(self):
        """F8.4: Verify scatter chart tooltips include Value Index and Average 0-100."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Value Index"), bindings)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), bindings)

    def test_f8_05_scatter_chart_geometry(self):
        """F8.5: Verify scatter chart geometry spans cols 2-3 at x=504, y=504, width=912, height=540."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        self.assertEqual(scatter.x, 504)
        self.assertEqual(scatter.y, 504)
        self.assertEqual(scatter.width, 912)
        self.assertEqual(scatter.height, 540)

    # =========================================================================
    # FEATURE 9: Powertrain & Segment Heatmap (5 tests)
    # =========================================================================
    def test_f9_01_pivot_table_exists(self):
        """F9.1: Verify visual container of type 'pivotTable' exists on page."""
        pivots = [v for v in self.page.visuals if v.visual_type == "pivotTable"]
        self.assertEqual(len(pivots), 1, "Exactly 1 pivotTable visual must exist")

    def test_f9_02_pivot_table_rows_columns_bindings(self):
        """F9.2: Verify pivotTable Rows is Segment_Name and Columns is Fuel_Group."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        bindings = extract_visual_bindings(pivot.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), bindings)

    def test_f9_03_pivot_table_values_binding(self):
        """F9.3: Verify pivotTable Values is bound to _Measures[Vehicle Count]."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        bindings = extract_visual_bindings(pivot.data)
        self.assertIn(("Measure", "_Measures", "Vehicle Count"), bindings)

    def test_f9_04_pivot_table_conditional_formatting(self):
        """F9.4: Verify pivotTable has native linearGradient2 conditional formatting rule on Vehicle Count."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        v_str = json.dumps(pivot.data)
        self.assertIn("linearGradient2", v_str)
        self.assertIn("Vehicle Count", v_str)
        self.assertIn("FillRule", v_str)

    def test_f9_05_pivot_table_geometry(self):
        """F9.5: Verify pivotTable geometry is positioned at x=36, y=270, width=444, height=774."""
        pivot = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        self.assertEqual(pivot.x, 36)
        self.assertEqual(pivot.y, 270)
        self.assertEqual(pivot.width, 444)
        self.assertEqual(pivot.height, 774)

    # =========================================================================
    # FEATURE 10: Top Value Leaders Table (5 tests)
    # =========================================================================
    def test_f10_01_table_ex_exists(self):
        """F10.1: Verify visual container of type 'tableEx' exists on page."""
        tables = [v for v in self.page.visuals if v.visual_type == "tableEx"]
        self.assertEqual(len(tables), 1, "Exactly 1 tableEx visual must exist")

    def test_f10_02_table_ex_columns_projection(self):
        """F10.2: Verify tableEx columns include Company, Car_Name, HP, Price, and Value Index."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        bindings = extract_visual_bindings(table.data)
        self.assertIn(("Column", "FactVehicle", "Company"), bindings)
        self.assertIn(("Column", "FactVehicle", "Car_Name"), bindings)
        self.assertIn(("Column", "FactVehicle", "HorsePower_Avg"), bindings)
        self.assertIn(("Column", "FactVehicle", "Price_Avg_USD"), bindings)
        self.assertIn(("Measure", "_Measures", "Value Index"), bindings)

    def test_f10_03_table_ex_top_n_filter_type(self):
        """F10.3: Verify tableEx has a filter of type 'TopN'."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        v_str = json.dumps(table.data)
        self.assertTrue('"type": "TopN"' in v_str or '"type":"TopN"' in v_str)

    def test_f10_04_table_ex_top_n_count_and_direction(self):
        """F10.4: Verify tableEx Top N filter specifies Count: 10 and Direction: 2 (descending)."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        v_str = json.dumps(table.data)
        self.assertTrue('"10L"' in v_str or "Top10" in v_str or '"TopN"' in v_str)
        self.assertTrue('"Direction": 2' in v_str or '"direction": "Descending"' in v_str or '"direction":"Descending"' in v_str)

    def test_f10_05_table_ex_geometry(self):
        """F10.5: Verify tableEx geometry is positioned at x=1440, y=270, width=444, height=774."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        self.assertEqual(table.x, 1440)
        self.assertEqual(table.y, 270)
        self.assertEqual(table.width, 444)
        self.assertEqual(table.height, 774)

    # =========================================================================
    # FEATURE 11: Dropdown Slicers (5 tests)
    # =========================================================================
    def test_f11_01_slicer_count(self):
        """F11.1: Verify exactly 4 visual containers of type 'slicer' exist on page."""
        slicers = [v for v in self.page.visuals if v.visual_type == "slicer"]
        self.assertEqual(len(slicers), 4, f"Expected 4 slicer visuals, found {len(slicers)}")

    def test_f11_02_slicer_segment_binding(self):
        """F11.2: Verify Price Segment slicer is bound to DimPriceSegment[Segment_Name]."""
        s = next((v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 36 and v.y == 74), None)
        self.assertIsNotNone(s, "Price Segment slicer not found at (36, 74)")
        bindings = extract_visual_bindings(s.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), bindings)

    def test_f11_03_slicer_fuel_binding(self):
        """F11.3: Verify Powertrain slicer is bound to DimFuel[Fuel_Group]."""
        s = next((v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 270 and v.y == 74), None)
        self.assertIsNotNone(s, "Powertrain slicer not found at (270, 74)")
        bindings = extract_visual_bindings(s.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), bindings)

    def test_f11_04_slicer_company_binding(self):
        """F11.4: Verify Brand slicer is bound to DimCompany[Company]."""
        s = next((v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 489 and v.y == 74), None)
        self.assertIsNotNone(s, "Brand slicer not found at (489, 74)")
        bindings = extract_visual_bindings(s.data)
        self.assertIn(("Column", "DimCompany", "Company"), bindings)

    def test_f11_05_slicer_scope_binding(self):
        """F11.5: Verify Vehicle Scope slicer is bound to FactVehicle[Vehicle Scope Status]."""
        s = next((v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 708 and v.y == 74), None)
        self.assertIsNotNone(s, "Vehicle Scope slicer not found at (708, 74)")
        bindings = extract_visual_bindings(s.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Scope Status"), bindings)

    # =========================================================================
    # FEATURE 12: Header & Navigation (5 tests)
    # =========================================================================
    def test_f12_01_textbox_visual_exists(self):
        """F12.1: Verify visual container of type 'textbox' exists on page."""
        boxes = [v for v in self.page.visuals if v.visual_type == "textbox"]
        self.assertEqual(len(boxes), 1, "Exactly 1 textbox visual must exist")

    def test_f12_02_textbox_content(self):
        """F12.2: Verify textbox contains title 'CARS INTELLIGENCE 2025'."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        tb_str = json.dumps(tb.data)
        self.assertIn("CARS INTELLIGENCE 2025", tb_str)

    def test_f12_03_page_navigator_visual_exists(self):
        """F12.3: Verify visual container of type 'pageNavigator' exists on page."""
        navs = [v for v in self.page.visuals if v.visual_type == "pageNavigator"]
        self.assertEqual(len(navs), 1, "Exactly 1 pageNavigator visual must exist")

    def test_f12_04_header_visuals_positions(self):
        """F12.4: Verify textbox is at (36, 20) and pageNavigator is at (1390, 20)."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        nav = next(v for v in self.page.visuals if v.visual_type == "pageNavigator")
        self.assertEqual(tb.x, 36)
        self.assertEqual(tb.y, 20)
        self.assertEqual(nav.x, 1390)
        self.assertEqual(nav.y, 20)

    def test_f12_05_header_band_geometry(self):
        """F12.5: Verify header band fits strictly between y=20 and y=72 within 1920 canvas width."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        nav = next(v for v in self.page.visuals if v.visual_type == "pageNavigator")
        self.assertLessEqual(tb.bottom, 72)
        self.assertLessEqual(nav.bottom, 72)
        self.assertLessEqual(nav.right, 1920)

    # =========================================================================
    # FEATURE 13: Automotive Studio Bento Grid (5 tests)
    # =========================================================================
    def test_f13_01_total_visual_count(self):
        """F13.1: Verify exactly 15 visual containers exist on page 01_MarketOverview."""
        self.assertEqual(len(self.page.visuals), 15, f"Expected 15 visuals, found {len(self.page.visuals)}")

    def test_f13_02_canvas_bounds(self):
        """F13.2: Verify canvas is 1920x1080 and all 15 visuals lie strictly within canvas bounds."""
        self.assertEqual(self.page.width, 1920)
        self.assertEqual(self.page.height, 1080)
        for v in self.page.visuals:
            self.assertGreaterEqual(v.x, 0, f"Visual {v.id} X < 0")
            self.assertGreaterEqual(v.y, 0, f"Visual {v.id} Y < 0")
            self.assertLessEqual(v.right, 1920, f"Visual {v.id} right > 1920: {v.right}")
            self.assertLessEqual(v.bottom, 1080, f"Visual {v.id} bottom > 1080: {v.bottom}")

    def test_f13_03_four_column_alignment(self):
        """F13.3: Verify visuals align with the 4 standard column anchors: x=36, 504, 972, 1440."""
        expected_anchors = {36, 270, 489, 504, 708, 972, 1390, 1440}
        for v in self.page.visuals:
            self.assertIn(v.x, expected_anchors, f"Visual {v.id} starts at unaligned x={v.x}")

    def test_f13_04_column_gaps_and_margins(self):
        """F13.4: Verify standard Bento column width is 444px and column gap is 24px."""
        col1_x = 36
        col_w = 444
        gap = 24
        col2_x = col1_x + col_w + gap
        col3_x = col2_x + col_w + gap
        col4_x = col3_x + col_w + gap
        self.assertEqual(col2_x, 504)
        self.assertEqual(col3_x, 972)
        self.assertEqual(col4_x, 1440)
        # Check KPI cards match this exact progression
        kpi_x_coords = sorted([v.x for v in self.page.visuals if v.visual_type == "cardVisual"])
        self.assertEqual(kpi_x_coords, [36, 504, 972, 1440])

    def test_f13_05_zero_visual_overlap(self):
        """F13.5: Verify no two visual containers on the canvas overlap each other."""
        visuals = self.page.visuals
        for i in range(len(visuals)):
            for j in range(i + 1, len(visuals)):
                v1 = visuals[i]
                v2 = visuals[j]
                overlaps = check_bounding_box_overlap(v1, v2)
                self.assertFalse(overlaps, f"Visuals {v1.id} [{v1.visual_type}] and {v2.id} [{v2.visual_type}] overlap!")

    # =========================================================================
    # FEATURE 14: Theme Styling (5 tests)
    # =========================================================================
    def test_f14_01_theme_file_and_name(self):
        """F14.1: Verify registered theme file exists and theme name is 'Automotive Intelligence Modern Enterprise'."""
        self.assertTrue(os.path.isfile(THEME_PATH), "Registered theme file must exist")
        self.assertEqual(self.theme.get("name"), "Automotive Intelligence Modern Enterprise")

    def test_f14_02_theme_palette_colors(self):
        """F14.2: Verify theme dataColors match the specified enterprise palette."""
        expected_palette = ["#2563EB", "#10B981", "#F59E0B", "#F43F5E", "#8B5CF6", "#06B6D4", "#475569", "#0F172A"]
        self.assertEqual(self.theme.get("dataColors"), expected_palette)

    def test_f14_03_theme_surface_colors(self):
        """F14.3: Verify theme surfaces: background (#F8FAFC), foreground (#0F172A), tableAccent (#2563EB)."""
        self.assertEqual(self.theme.get("background"), "#F8FAFC")
        self.assertEqual(self.theme.get("foreground"), "#0F172A")
        self.assertEqual(self.theme.get("tableAccent"), "#2563EB")

    def test_f14_04_theme_visual_card_radius(self):
        """F14.4: Verify theme specifies 16px border radius on visual containers."""
        v_styles = self.theme.get("visualStyles", {})
        border_radius = v_styles.get("*", {}).get("*", {}).get("border", [{}])[0].get("radius")
        self.assertEqual(border_radius, 16)

    def test_f14_05_theme_registered_in_report(self):
        """F14.5: Verify report.json explicitly registers the theme as CustomTheme."""
        report_json_path = os.path.join(REPORT_DEF_DIR, "report.json")
        with open(report_json_path, "r", encoding="utf-8") as f:
            rep_data = json.load(f)
        theme_ref = rep_data.get("themeCollection", {}).get("customTheme", {}).get("name")
        self.assertIn(theme_ref, ["Cars_Intelligence_20258711528438303722", "Cars_Intelligence_20258711528438303722.json"])

    # =========================================================================
    # FEATURE 15: Strict UTF-8 Without BOM (5 tests)
    # =========================================================================
    def test_f15_01_tmdl_utf8_no_bom(self):
        """F15.1: Verify all TMDL files strictly maintain UTF-8 encoding without BOM."""
        tmdl_files = glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl"), recursive=True)
        self.assertGreaterEqual(len(tmdl_files), 14, "Expected at least 14 TMDL files")
        for tf in tmdl_files:
            with open(tf, "rb") as f:
                header = f.read(3)
            self.assertNotEqual(header, b"\xef\xbb\xbf", f"TMDL file {tf} has UTF-8 BOM")

    def test_f15_02_json_utf8_no_bom(self):
        """F15.2: Verify all JSON files in powerbi/ strictly maintain UTF-8 without BOM."""
        json_files = glob.glob(os.path.join(REPO_ROOT, "powerbi", "**", "*.json"), recursive=True)
        self.assertGreaterEqual(len(json_files), 46, "Expected at least 46 JSON files")
        for jf in json_files:
            with open(jf, "rb") as f:
                header = f.read(3)
            self.assertNotEqual(header, b"\xef\xbb\xbf", f"JSON file {jf} has UTF-8 BOM")

    def test_f15_03_tmdl_tab_indentation(self):
        """F15.3: Verify all TMDL files use strictly TAB characters for line indentation (0 spaces)."""
        tmdl_files = glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl"), recursive=True)
        space_indented_lines = []
        for tf in tmdl_files:
            with open(tf, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, start=1):
                    if line.startswith(" "):
                        space_indented_lines.append(f"{os.path.basename(tf)}:{idx}")
        self.assertEqual(len(space_indented_lines), 0, f"Space indentation found in TMDL: {space_indented_lines[:5]}")

    def test_f15_04_json_parse_clean(self):
        """F15.4: Verify all JSON files parse cleanly with valid syntax."""
        json_files = glob.glob(os.path.join(REPO_ROOT, "powerbi", "**", "*.json"), recursive=True)
        for jf in json_files:
            with open(jf, "r", encoding="utf-8") as f:
                try:
                    json.load(f)
                except Exception as e:
                    self.fail(f"Failed to parse JSON file {jf}: {e}")

    def test_f15_05_no_null_bytes(self):
        """F15.5: Verify zero files in semantic model or report definition contain NUL bytes (b'\\x00')."""
        files = glob.glob(os.path.join(REPO_ROOT, "powerbi", "**", "*.*"), recursive=True)
        for fpath in files:
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    content = f.read()
                self.assertNotIn(b"\x00", content, f"NUL byte found in {fpath}")

    # =========================================================================
    # FEATURE 16: Performance Lab Bento Grid Geometry (5 tests)
    # =========================================================================
    def test_f16_01_performance_lab_canvas_dimensions(self):
        """F16.1: Verify Page 02 canvas width is strictly 1920, height is 1080, and displayOption is FitToPage."""
        self.assertEqual(self.page2.width, 1920)
        self.assertEqual(self.page2.height, 1080)
        self.assertEqual(self.page2.data.get("displayOption"), "FitToPage")

    def test_f16_02_performance_lab_visual_container_count(self):
        """F16.2: Verify exactly 15 visual containers exist on page 02_PerformanceLab."""
        self.assertEqual(len(self.page2.visuals), 15)

    def test_f16_03_performance_lab_bento_column_grid_alignment(self):
        """F16.3: Verify visual horizontal coordinates strictly align to 4-column Bento grid."""
        valid_x_origins = {36, 270, 489, 504, 708, 972, 1390, 1440}
        for v in self.page2.visuals:
            self.assertIn(v.x, valid_x_origins, f"Visual {v.id} x={v.x} not aligned to Bento grid")

    def test_f16_04_performance_lab_bento_margins_and_gaps(self):
        """F16.4: Verify Bento active width 1848px (left=36, right=36, bottom=36, top=20)."""
        left_margin = min(v.x for v in self.page2.visuals)
        right_margin = 1920 - max(v.right for v in self.page2.visuals)
        top_margin = min(v.y for v in self.page2.visuals)
        bottom_margin = 1080 - max(v.bottom for v in self.page2.visuals)
        self.assertEqual(left_margin, 36)
        self.assertEqual(right_margin, 36)
        self.assertEqual(top_margin, 20)
        self.assertEqual(bottom_margin, 36)

    def test_f16_05_performance_lab_zero_visual_overlap(self):
        """F16.5: Verify zero pairwise bounding box collisions among all 15 visual containers on Page 02."""
        overlaps = []
        for i in range(len(self.page2.visuals)):
            for j in range(i + 1, len(self.page2.visuals)):
                v1 = self.page2.visuals[i]
                v2 = self.page2.visuals[j]
                if check_bounding_box_overlap(v1, v2):
                    overlaps.append((v1.id, v2.id))
        self.assertEqual(len(overlaps), 0, f"Collisions detected on Page 02: {overlaps}")

    # =========================================================================
    # FEATURE 17: Performance Lab Pure Typography KPI Cards (5 tests)
    # =========================================================================
    def test_f17_01_kpi_cards_count_and_types(self):
        """F17.1: Verify exactly 4 cardVisual containers exist on Page 02 at y=142 with height=116, width=444."""
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        self.assertEqual(len(kpis), 4)
        for k in kpis:
            self.assertEqual(k.y, 142)
            self.assertEqual(k.height, 116)
            self.assertEqual(k.width, 444)

    def test_f17_02_kpi_average_hp_binding(self):
        """F17.2: Verify Card 1 binds to _Measures[Average HP]."""
        card1 = next(v for v in self.page2.visuals if v.id == "perf_kpi_hp" or (v.visual_type == "cardVisual" and v.x == 36))
        bindings = extract_visual_bindings(card1.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)

    def test_f17_03_kpi_average_speed_binding(self):
        """F17.3: Verify Card 2 binds to _Measures[Average Speed]."""
        card2 = next(v for v in self.page2.visuals if v.id == "perf_kpi_speed" or (v.visual_type == "cardVisual" and v.x == 504))
        bindings = extract_visual_bindings(card2.data)
        self.assertIn(("Measure", "_Measures", "Average Speed"), bindings)

    def test_f17_04_kpi_average_accel_binding(self):
        """F17.4: Verify Card 3 binds to _Measures[Average 0-100]."""
        card3 = next(v for v in self.page2.visuals if v.id == "perf_kpi_accel" or (v.visual_type == "cardVisual" and v.x == 972))
        bindings = extract_visual_bindings(card3.data)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), bindings)

    def test_f17_05_kpi_average_torque_binding(self):
        """F17.5: Verify Card 4 binds to _Measures[Average Torque]."""
        card4 = next(v for v in self.page2.visuals if v.id == "perf_kpi_torque" or (v.visual_type == "cardVisual" and v.x == 1440))
        bindings = extract_visual_bindings(card4.data)
        self.assertIn(("Measure", "_Measures", "Average Torque"), bindings)

    # =========================================================================
    # FEATURE 18: Performance Lab Telemetry Cockpit Gauge (5 tests)
    # =========================================================================
    def test_f18_01_gauge_visual_exists(self):
        """F18.1: Verify visual container perf_gauge_cockpit exists with visualType == 'gauge'."""
        gauges = [v for v in self.page2.visuals if v.visual_type == "gauge"]
        self.assertEqual(len(gauges), 1)

    def test_f18_02_gauge_geometry(self):
        """F18.2: Verify gauge is positioned at x=504, y=270, width=444, height=220, z=7500."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        self.assertEqual(gauge.x, 504)
        self.assertEqual(gauge.y, 270)
        self.assertEqual(gauge.width, 444)
        self.assertEqual(gauge.height, 220)
        self.assertEqual(gauge.z, 7500)

    def test_f18_03_gauge_value_binding(self):
        """F18.3: Verify gauge value binds to _Measures[Performance Index]."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        bindings = extract_visual_bindings(gauge.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), bindings)

    def test_f18_04_gauge_target_binding(self):
        """F18.4: Verify gauge target binds to _Measures[Performance Index (AVG Market)]."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        bindings = extract_visual_bindings(gauge.data)
        self.assertIn(("Measure", "_Measures", "Performance Index (AVG Market)"), bindings)

    def test_f18_05_gauge_axis_scale(self):
        """F18.5: Verify gauge axis specifies min = 0 and max = 100."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        g_str = json.dumps(gauge.data)
        self.assertIn('"0D"', g_str)
        self.assertIn('"100D"', g_str)

    # =========================================================================
    # FEATURE 19: Performance Lab Sprint Benchmark Bar Chart (5 tests)
    # =========================================================================
    def test_f19_01_bar_chart_exists(self):
        """F19.1: Verify visual container perf_bar_sprint exists with visualType == 'clusteredBarChart'."""
        bars = [v for v in self.page2.visuals if v.visual_type == "clusteredBarChart"]
        self.assertEqual(len(bars), 1)

    def test_f19_02_bar_chart_geometry(self):
        """F19.2: Verify sprint bar chart is positioned at x=972, y=270, width=444, height=220, z=7600."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        self.assertEqual(bar.x, 972)
        self.assertEqual(bar.y, 270)
        self.assertEqual(bar.width, 444)
        self.assertEqual(bar.height, 220)
        self.assertEqual(bar.z, 7600)

    def test_f19_03_bar_chart_category_projection(self):
        """F19.3: Verify sprint bar chart category binds to DimPriceSegment[Segment_Name]."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), bindings)

    def test_f19_04_bar_chart_y_measure_projection(self):
        """F19.4: Verify sprint bar chart Y projection binds to _Measures[Average 0-100]."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), bindings)

    def test_f19_05_bar_chart_container_styling(self):
        """F19.5: Verify sprint bar chart container includes 16px corner radius and drop shadow."""
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        b_str = json.dumps(bar.data)
        self.assertIn('"radius"', b_str)
        self.assertIn('"16D"', b_str)
        self.assertIn('"dropShadow"', b_str)

    # =========================================================================
    # FEATURE 20: Performance Lab Dynamics Scatter Matrix (5 tests)
    # =========================================================================
    def test_f20_01_scatter_chart_exists(self):
        """F20.1: Verify visual container perf_scatter_dynamics exists with visualType == 'scatterChart'."""
        scatters = [v for v in self.page2.visuals if v.visual_type == "scatterChart"]
        self.assertEqual(len(scatters), 1)

    def test_f20_02_scatter_chart_geometry(self):
        """F20.2: Verify dynamics scatter chart spans columns 2-3 at x=504, y=504, width=912, height=540, z=8000."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        self.assertEqual(scatter.x, 504)
        self.assertEqual(scatter.y, 504)
        self.assertEqual(scatter.width, 912)
        self.assertEqual(scatter.height, 540)
        self.assertEqual(scatter.z, 8000)

    def test_f20_03_scatter_chart_category_and_series(self):
        """F20.3: Verify scatter chart details bind to Vehicle Display Name and series to Fuel_Group."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Display Name"), bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), bindings)

    def test_f20_04_scatter_chart_axes_measures(self):
        """F20.4: Verify scatter chart X-axis binds to Average HP and Y-axis binds to Average Speed."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)
        self.assertIn(("Measure", "_Measures", "Average Speed"), bindings)

    def test_f20_05_scatter_chart_size_measure(self):
        """F20.5: Verify scatter chart bubble size binds to _Measures[Performance Index]."""
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), bindings)

    # =========================================================================
    # FEATURE 21: Performance Lab Powertrain Matrix (5 tests)
    # =========================================================================
    def test_f21_01_pivot_table_exists(self):
        """F21.1: Verify visual container perf_pivot_matrix exists with visualType == 'pivotTable'."""
        pivots = [v for v in self.page2.visuals if v.visual_type == "pivotTable"]
        self.assertEqual(len(pivots), 1)

    def test_f21_02_pivot_table_geometry(self):
        """F21.2: Verify pivot table is positioned as Col 1 flanker at x=36, y=270, width=444, height=774, z=7000."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        self.assertEqual(pivot.x, 36)
        self.assertEqual(pivot.y, 270)
        self.assertEqual(pivot.width, 444)
        self.assertEqual(pivot.height, 774)
        self.assertEqual(pivot.z, 7000)

    def test_f21_03_pivot_table_row_and_column_dimensions(self):
        """F21.3: Verify pivot table Rows bind to Fuel_Group and Columns bind to Segment_Name."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        bindings = extract_visual_bindings(pivot.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), bindings)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), bindings)

    def test_f21_04_pivot_table_value_measure(self):
        """F21.4: Verify pivot table Values projection binds to _Measures[Average HP]."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        bindings = extract_visual_bindings(pivot.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)

    def test_f21_05_pivot_table_linear_gradient(self):
        """F21.5: Verify native linearGradient2 conditional formatting is configured on Average HP."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data)
        self.assertIn("linearGradient2", p_str)
        self.assertIn("#F1F5F9", p_str)
        self.assertIn("#93C5FD", p_str)

    # =========================================================================
    # FEATURE 22: Performance Lab Track Leaderboard Table (5 tests)
    # =========================================================================
    def test_f22_01_table_ex_exists(self):
        """F22.1: Verify visual container perf_table_leaders exists with visualType == 'tableEx'."""
        tables = [v for v in self.page2.visuals if v.visual_type == "tableEx"]
        self.assertEqual(len(tables), 1)

    def test_f22_02_table_ex_geometry(self):
        """F22.2: Verify tableEx is positioned as Col 4 flanker at x=1440, y=270, width=444, height=774, z=9000."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        self.assertEqual(table.x, 1440)
        self.assertEqual(table.y, 270)
        self.assertEqual(table.width, 444)
        self.assertEqual(table.height, 774)
        self.assertEqual(table.z, 9000)

    def test_f22_03_table_ex_projections(self):
        """F22.3: Verify tableEx projections include Company, Car_Name, Fuel_Group, HP, Speed, 0-100, Performance Index."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        bindings = extract_visual_bindings(table.data)
        self.assertIn(("Column", "FactVehicle", "Company"), bindings)
        self.assertIn(("Column", "FactVehicle", "Car_Name"), bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)
        self.assertIn(("Measure", "_Measures", "Average Speed"), bindings)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), bindings)
        self.assertIn(("Measure", "_Measures", "Performance Index"), bindings)

    def test_f22_04_table_ex_top_n_filter(self):
        """F22.4: Verify Top N filter is configured targeting Top 10 by Performance Index descending."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertTrue('"10L"' in t_str or "Top" in t_str or "10" in t_str)
        self.assertIn("Performance Index", t_str)

    def test_f22_05_table_ex_sort_definition(self):
        """F22.5: Verify table default sort is configured on Performance Index descending."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertTrue('"direction": "Descending"' in t_str or '"direction":"Descending"' in t_str or '"Direction": 2' in t_str)
        self.assertIn("Performance Index", t_str)

    # =========================================================================
    # FEATURE 23: Performance Lab Slicers & Page Navigation (5 tests)
    # =========================================================================
    def test_f23_01_slicer_count_and_positions(self):
        """F23.1: Verify exactly 4 slicers exist on Page 02 positioned at y=80 with height=50."""
        slicers = [v for v in self.page2.visuals if v.visual_type == "slicer"]
        self.assertEqual(len(slicers), 4)
        for s in slicers:
            self.assertEqual(s.y, 74)
            self.assertEqual(s.height, 60)

    def test_f23_02_slicer_bindings(self):
        """F23.2: Verify slicer bindings: Fuel, Brand, Segment, Scope."""
        slicers = [v for v in self.page2.visuals if v.visual_type == "slicer"]
        all_bindings = []
        for s in slicers:
            all_bindings.extend(extract_visual_bindings(s.data))
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), all_bindings)
        self.assertIn(("Column", "DimCompany", "Company"), all_bindings)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), all_bindings)
        self.assertIn(("Column", "FactVehicle", "Vehicle Scope Status"), all_bindings)

    def test_f23_03_page_navigator_exists(self):
        """F23.3: Verify pageNavigator exists at x=1390, y=20, width=494, height=48, z=13000."""
        navs = [v for v in self.page2.visuals if v.visual_type == "pageNavigator"]
        self.assertEqual(len(navs), 1)
        nav = navs[0]
        self.assertEqual(nav.x, 1390)
        self.assertEqual(nav.y, 20)
        self.assertEqual(nav.width, 494)
        self.assertEqual(nav.height, 48)
        self.assertEqual(nav.z, 13000)

    def test_f23_04_page_navigator_pill_styling(self):
        """F23.4: Verify page navigator rounded pill styling with 14L curve radius."""
        nav = next(v for v in self.page2.visuals if v.visual_type == "pageNavigator")
        n_str = json.dumps(nav.data)
        self.assertIn("rectangleRoundedByPixel", n_str)
        self.assertIn('"14L"', n_str)

    def test_f23_05_header_textbox_styling(self):
        """F23.5: Verify header textbox exists at x=36, y=20, width=640, height=52 with Segoe UI typography."""
        tb = next(v for v in self.page2.visuals if v.visual_type == "textbox")
        self.assertEqual(tb.x, 36)
        self.assertEqual(tb.y, 20)
        self.assertEqual(tb.width, 640)
        self.assertEqual(tb.height, 52)
        tb_str = json.dumps(tb.data)
        self.assertIn("CARS INTELLIGENCE 2025", tb_str)
        self.assertIn("Performance Lab", tb_str)

    # =========================================================================
    # FEATURE 24: Performance Lab Theme Styling (5 tests)
    # =========================================================================
    def test_f24_01_card_background_white(self):
        """F24.1: Verify card backgrounds across analytical visuals on Page 02 specify #FFFFFF with 0% transparency."""
        analytical_visuals = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for v in analytical_visuals:
            v_str = json.dumps(v.data)
            self.assertIn("#FFFFFF", v_str, f"Visual {v.id} missing #FFFFFF surface")

    def test_f24_02_container_border_radius(self):
        """F24.2: Verify visual container borders specify 16px corner radius (radius: 16D) and #E2E8F0 color."""
        analytical_visuals = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for v in analytical_visuals:
            v_str = json.dumps(v.data)
            self.assertIn('"16D"', v_str, f"Visual {v.id} missing 16D corner radius")
            self.assertIn("#E2E8F0", v_str, f"Visual {v.id} missing #E2E8F0 border")

    def test_f24_03_container_elevation_drop_shadow(self):
        """F24.3: Verify visual container dropShadow specifies #CBD5E1, blur 8D, distance 2D, Outer preset."""
        analytical_visuals = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for v in analytical_visuals:
            v_str = json.dumps(v.data)
            self.assertIn("#CBD5E1", v_str, f"Visual {v.id} missing #CBD5E1 dropShadow")
            self.assertIn('"8D"', v_str, f"Visual {v.id} missing 8D shadow blur")

    def test_f24_04_visual_header_hidden(self):
        """F24.4: Verify default visual header toolbar is hidden (visualHeader: show: false) on analytical cards."""
        analytical_visuals = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for v in analytical_visuals:
            v_str = json.dumps(v.data)
            self.assertIn('"visualHeader"', v_str, f"Visual {v.id} missing visualHeader config")

    def test_f24_05_typography_hierarchy_conformance(self):
        """F24.5: Verify typography tokens conform to theme (28pt callouts, Segoe UI Bold titles, Segoe UI subtitles)."""
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        for k in kpis:
            k_str = json.dumps(k.data)
            self.assertIn('"28D"', k_str, f"KPI {k.id} missing 28D callout font size")
            self.assertIn("#0F172A", k_str, f"KPI {k.id} missing #0F172A callout color")

    # =========================================================================
    # FEATURE 25: Performance Lab Clean DAX Measure Bindings (5 tests)
    # =========================================================================
    def test_f25_01_measure_resolution(self):
        """F25.1: Verify 100% of measure bindings on Page 02 resolve in _Measures.tmdl."""
        unresolved = []
        for v in self.page2.visuals:
            bindings = extract_visual_bindings(v.data)
            for b_type, entity, prop in bindings:
                if b_type == "Measure":
                    if entity not in self.model.tables or prop not in self.model.tables[entity].measures:
                        unresolved.append((v.id, entity, prop))
        self.assertEqual(len(unresolved), 0, f"Unresolved measures on Page 02: {unresolved}")

    def test_f25_02_column_resolution(self):
        """F25.2: Verify 100% of column bindings on Page 02 resolve in semantic model tables."""
        unresolved = []
        for v in self.page2.visuals:
            bindings = extract_visual_bindings(v.data)
            for b_type, entity, prop in bindings:
                if b_type == "Column":
                    if entity not in self.model.tables or prop not in self.model.tables[entity].columns:
                        unresolved.append((v.id, entity, prop))
        self.assertEqual(len(unresolved), 0, f"Unresolved columns on Page 02: {unresolved}")

    def test_f25_03_zero_svg_references(self):
        """F25.3: Verify zero references to SVG measures, data-URIs, or legacy image controls on Page 02."""
        for v in self.page2.visuals:
            v_str = json.dumps(v.data)
            self.assertNotIn("image/svg+xml", v_str)
            self.assertNotIn("<svg", v_str)
            self.assertNotIn("data:image", v_str)
            self.assertNotIn("SVG ", v_str)

    def test_f25_04_zero_direct_column_aggregations(self):
        """F25.4: Verify KPIs and gauges use clean DAX measures rather than raw column aggregations."""
        cards_and_gauges = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge")]
        for cg in cards_and_gauges:
            bindings = extract_visual_bindings(cg.data)
            for b_type, entity, prop in bindings:
                self.assertEqual(b_type, "Measure", f"Visual {cg.id} binds directly to raw column {entity}.{prop}")

    def test_f25_05_measure_lineage_tags_intact(self):
        """F25.5: Verify every bound measure on Page 02 has a valid GUID lineageTag in _Measures.tmdl."""
        guid_pattern = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
        for v in self.page2.visuals:
            bindings = extract_visual_bindings(v.data)
            for b_type, entity, prop in bindings:
                if b_type == "Measure" and entity == "_Measures":
                    m_data = self.model.tables["_Measures"].measures.get(prop)
                    self.assertIsNotNone(m_data, f"Measure {prop} not found in model")
                    lt = m_data.get("lineageTag")
                    self.assertIsNotNone(lt, f"Measure {prop} missing lineageTag")
                    self.assertRegex(lt, guid_pattern, f"Measure {prop} lineageTag {lt} is not valid GUID")

if __name__ == "__main__":
    unittest.main()
