"""
Cars Intelligence 2025 - Tier 4: Real-World Application Scenarios Test Suite
End-to-end user workflows and persona-driven analytics journeys.
Covers 10 realistic application scenarios.
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

class TestTier4Scenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_semantic_model()
        cls.page = load_report_page()
        cls.page1 = cls.page
        cls.page2 = load_performance_lab_page()
        cls.theme = load_theme()

    def test_scenario_01_executive_dashboard_consumption(self):
        """Scenario 1: Executive Overview Journey - High-level cockpit rendering without scrollbars."""
        # 1. Header is clear and positioned at top-left
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        self.assertEqual(tb.x, 36)
        self.assertEqual(tb.y, 20)
        self.assertIn("CARS INTELLIGENCE 2025", json.dumps(tb.data))

        # 2. Page navigation exists at top-right
        nav = next(v for v in self.page.visuals if v.visual_type == "pageNavigator")
        self.assertEqual(nav.x, 1390)
        self.assertEqual(nav.y, 20)

        # 3. All 4 KPI cards render in single horizontal row
        kpis = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        self.assertEqual(len(kpis), 4)
        for k in kpis:
            self.assertEqual(k.y, 142)
            self.assertEqual(k.height, 116)

        # 4. Macro performance gauge renders in central cockpit
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        self.assertEqual(gauge.x, 504)
        self.assertEqual(gauge.y, 270)

        # 5. Canvas resolution strictly matches 1080p display
        self.assertEqual(self.page.width, 1920)
        self.assertEqual(self.page.height, 1080)
        for v in self.page.visuals:
            self.assertLessEqual(v.right, 1920)
            self.assertLessEqual(v.bottom, 1080)

    def test_scenario_02_automotive_value_hunter(self):
        """Scenario 2: Automotive Value Hunter - Isolating top value leaders and underpriced vehicles."""
        # 1. TableEx specifically filters for 'Best Value' vehicles
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertIn("Best Value", t_str)

        # 2. TableEx applies Top N = 10 sorted by Value Index descending
        self.assertTrue('"10L"' in t_str or "Top10" in t_str or '"TopN"' in t_str)
        self.assertIn("Value Index", t_str)
        self.assertTrue('"Direction": 2' in t_str or '"direction": "Descending"' in t_str or '"direction":"Descending"' in t_str)

        # 3. Scatter chart tooltips provide Value Index for micro analysis
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Value Index"), s_bindings)

        # 4. Measure Value Index is defined and incorporates Performance Index and Price
        m_vi = self.model.tables["_Measures"].measures["Value Index"]
        self.assertIn("[Performance Index]", m_vi["block"])
        self.assertIn("[Score Price (inverted)]", m_vi["block"])

    def test_scenario_03_electrification_transition_monitoring(self):
        """Scenario 3: Fleet Electrification Strategist - Tracking EV and Hybrid market penetration."""
        # 1. KPI 3 surfaces Electrified Share %
        kpi3 = next(v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 972)
        k3_bindings = extract_visual_bindings(kpi3.data)
        self.assertIn(("Measure", "_Measures", "Electrified Share %"), k3_bindings)

        # 2. Slicer 2 provides Powertrain selection on DimFuel[Fuel_Group]
        slicer_fuel = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 270)
        s_bindings = extract_visual_bindings(slicer_fuel.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), s_bindings)

        # 3. Heatmap PivotTable breaks down segments across Fuel Groups
        heatmap = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        h_bindings = extract_visual_bindings(heatmap.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), h_bindings)
        self.assertIn(("Measure", "_Measures", "Vehicle Count"), h_bindings)

        # 4. Measure Electrified Share % DAX logic filters for EV and Hybrid groups
        m_es = self.model.tables["_Measures"].measures["Electrified Share %"]
        self.assertIn("Fuel_Group", m_es["block"])
        self.assertIn("DIVIDE(", m_es["block"])

    def test_scenario_04_market_segmentation_deep_dive(self):
        """Scenario 4: Pricing Analyst Journey - Segment horsepower and model count distribution."""
        # 1. Segment slicer targets DimPriceSegment[Segment_Name]
        slicer_seg = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 36)
        s_bindings = extract_visual_bindings(slicer_seg.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), s_bindings)

        # 2. Clustered bar chart ranks segments by Average HP
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        b_bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), b_bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), b_bindings)

        # 3. Heatmap rows categorize by DimPriceSegment[Segment_Name]
        heatmap = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        h_bindings = extract_visual_bindings(heatmap.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), h_bindings)

        # 4. Relationship connects FactVehicle to DimPriceSegment
        rel = next((r for r in self.model.relationships if "DimPriceSegment" in r["toColumn"]), None)
        self.assertIsNotNone(rel)
        self.assertEqual(rel["fromColumn"], "FactVehicle.Segment_ID")

    def test_scenario_05_brand_portfolio_oem_benchmarking(self):
        """Scenario 5: OEM Executive Journey - Competitive brand positioning and pricing."""
        # 1. Brand slicer targets DimCompany[Company]
        slicer_brand = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 489)
        s_bindings = extract_visual_bindings(slicer_brand.data)
        self.assertIn(("Column", "DimCompany", "Company"), s_bindings)

        # 2. Scatter chart plots vehicles by Vehicle Display Name and Market Position series
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Display Name"), s_bindings)
        self.assertIn(("Column", "FactVehicle", "Market Position (Static)"), s_bindings)

        # 3. FactVehicle defines calculated column Vehicle Display Name combining Company, Name, Engine
        fact_cols = self.model.tables["FactVehicle"].columns
        self.assertIn("Vehicle Display Name", fact_cols)
        self.assertIn("Market Position (Static)", fact_cols)

    def test_scenario_06_supercar_outlier_filtering_workflow(self):
        """Scenario 6: Outlier Filtration Workflow - Scatter chart excludes supercars above $200,000."""
        # 1. Scatter chart contains filter on Price_Avg_USD <= 200000
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        s_str = json.dumps(scatter.data)
        self.assertIn("Price_Avg_USD", s_str)
        self.assertTrue("200000" in s_str or "200,000" in s_str or "200000D" in s_str or "200000L" in s_str)

        # 2. Heatmap and KPI cards do NOT have this filter, preserving full fleet context
        heatmap = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        h_str = json.dumps(heatmap.data)
        self.assertNotIn("200000", h_str)

        kpis = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        for k in kpis:
            k_str = json.dumps(k.data)
            self.assertNotIn("200000", k_str)

    def test_scenario_07_production_model_scope_auditing(self):
        """Scenario 7: Portfolio Scope Auditing - Auditing production models via Vehicle Scope Status."""
        # 1. Scope slicer targets FactVehicle[Vehicle Scope Status]
        slicer_scope = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 708)
        s_bindings = extract_visual_bindings(slicer_scope.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Scope Status"), s_bindings)

        # 2. FactVehicle defines Vehicle Scope Status calculated column
        fact_cols = self.model.tables["FactVehicle"].columns
        self.assertIn("Vehicle Scope Status", fact_cols)
        self.assertTrue(fact_cols["Vehicle Scope Status"]["isCalculated"])

        # 3. Slicer uses compact pill header styling
        s_str = json.dumps(slicer_scope.data)
        self.assertIn("Dropdown", s_str)

    def test_scenario_08_design_system_and_theme_cohesion(self):
        """Scenario 8: UI/UX Lead Brand Review - Bento grid card elevation and color cohesion."""
        # 1. Background color is Slate 50
        self.assertEqual(self.theme.get("background"), "#F8FAFC")

        # 2. Primary brand blue is #2563EB
        self.assertEqual(self.theme.get("tableAccent"), "#2563EB")
        self.assertEqual(self.theme.get("dataColors", [])[0], "#2563EB")

        # 3. Visual card containers have 16px corner radius and white background
        bento_cards = [v for v in self.page.visuals if v.visual_type in {
            "cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx"
        }]
        for card in bento_cards:
            c_str = json.dumps(card.data)
            self.assertIn("16D", c_str)
            self.assertIn("#FFFFFF", c_str)
            self.assertIn("#CBD5E1", c_str)

    def test_scenario_09_production_release_zero_defect_audit(self):
        """Scenario 9: Release Engineer Deployment Audit - Zero legacy SVG, zero BOM, valid PBIP."""
        # 1. Zero SVG measures across model
        measures = self.model.tables["_Measures"].measures
        self.assertFalse(any("svg" in m.lower() for m in measures.keys()))

        # 2. Zero SVG columns in FactVehicle
        columns = self.model.tables["FactVehicle"].columns
        self.assertFalse(any("svg" in c.lower() for c in columns.keys()))

        # 3. scripts/verify_report.py passes with 0 failures and 0 warnings
        res = subprocess.run(["python", VERIFY_SCRIPT_PATH], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("0 FAILED", res.stdout)
        self.assertIn("0 WARNINGS", res.stdout)

    def test_scenario_10_cross_filtering_star_schema_compatibility(self):
        """Scenario 10: Star Schema Integrity - Relationships and cross-filtering enabled."""
        # 1. Relationships connect dimension tables to FactVehicle
        connected_dims = set()
        for rel in self.model.relationships:
            from_table, _ = rel["fromColumn"].split(".", 1)
            to_table, _ = rel["toColumn"].split(".", 1)
            if from_table == "FactVehicle":
                connected_dims.add(to_table)
            elif to_table == "FactVehicle":
                connected_dims.add(from_table)
        self.assertIn("DimCompany", connected_dims)
        self.assertIn("DimFuel", connected_dims)
        self.assertIn("DimPriceSegment", connected_dims)

        # 2. Bento visuals enable drillFilterOtherVisuals
        for v in self.page.visuals:
            self.assertTrue(v.data.get("visual", {}).get("drillFilterOtherVisuals", True))

    def test_scenario_11_vehicle_performance_engineering_benchmark(self):
        """Scenario 11: Vehicle Performance Engineering Benchmark - EV vs ICE filtering, speed vs HP trade-offs, and Top 10 sprint leaderboard audit."""
        # 1. Slicer allows filtering EV vs ICE powertrains via DimFuel[Fuel_Group]
        slicer_fuel = next(v for v in self.page2.visuals if v.id == "perf_slicer_fuel" or (v.visual_type == "slicer" and v.x == 270))
        s_bindings = extract_visual_bindings(slicer_fuel.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), s_bindings)

        # 2. Dynamics Scatter Matrix displays speed vs HP trade-offs
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        sc_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), sc_bindings)
        self.assertIn(("Measure", "_Measures", "Average Speed"), sc_bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), sc_bindings)
        self.assertIn(("Measure", "_Measures", "Performance Index"), sc_bindings)

        # 3. Track Leaderboard TableEx audits Top 10 sprint leaders sorted by Performance Index
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        t_bindings = extract_visual_bindings(table.data)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), t_bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), t_bindings)
        self.assertIn(("Measure", "_Measures", "Average Speed"), t_bindings)
        self.assertIn(("Measure", "_Measures", "Performance Index"), t_bindings)
        t_str = json.dumps(table.data)
        self.assertTrue('"10L"' in t_str or "Top" in t_str or "10" in t_str)
        self.assertTrue('"direction": "Descending"' in t_str or '"direction":"Descending"' in t_str or '"Direction": 2' in t_str)

        # 4. Telemetry cockpit gauge provides macro fleet benchmark
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        g_bindings = extract_visual_bindings(gauge.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), g_bindings)
        self.assertIn(("Measure", "_Measures", "Performance Index (AVG Market)"), g_bindings)

    def test_scenario_12_powertrain_performance_heatmap_matrix_exploration(self):
        """Scenario 12: Powertrain & Segment Engineering Specialist - Matrix exploration with linearGradient2."""
        # 1. PivotTable matrix organizes Fuel_Group rows across Segment_Name columns
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        p_bindings = extract_visual_bindings(pivot.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), p_bindings)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), p_bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), p_bindings)

        # 2. Matrix applies linearGradient2 conditional formatting
        p_str = json.dumps(pivot.data)
        self.assertIn("linearGradient2", p_str)
        self.assertIn("#F1F5F9", p_str)
        self.assertIn("#93C5FD", p_str)

        # 3. Sprint bar chart compares 0-100 sprint times by Segment_Name
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        b_bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), b_bindings)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), b_bindings)

    def test_scenario_13_track_and_acceleration_leaderboard_audit(self):
        """Scenario 13: Track Enthusiast & Competitive Benchmarking - Full telemetry leaderboard audit."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        bindings = extract_visual_bindings(table.data)

        # Verify all essential vehicle specifications are projected
        self.assertIn(("Column", "FactVehicle", "Company"), bindings)
        self.assertIn(("Column", "FactVehicle", "Car_Name"), bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), bindings)
        self.assertIn(("Measure", "_Measures", "Average Speed"), bindings)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), bindings)
        self.assertIn(("Measure", "_Measures", "Performance Index"), bindings)

        # Verify default sort is Performance Index descending
        sort_field = table.data.get("visual", {}).get("query", {}).get("sortDefinition", {}).get("sort", [{}])[0].get("field", {}).get("Measure", {}).get("Property")
        self.assertEqual(sort_field, "Performance Index")

    def test_scenario_14_multi_page_enterprise_report_cohesion(self):
        """Scenario 14: BI Solution Architect Multi-Page Cohesion - Canvas, grid, navigation, and theme consistency."""
        # 1. Canvas dimensions match 1080p exactly across both pages
        self.assertEqual(self.page1.width, 1920)
        self.assertEqual(self.page1.height, 1080)
        self.assertEqual(self.page2.width, 1920)
        self.assertEqual(self.page2.height, 1080)

        # 2. Both pages contain exactly 15 visual containers
        self.assertEqual(len(self.page1.visuals), 15)
        self.assertEqual(len(self.page2.visuals), 15)

        # 3. Bidirectional page navigation visuals match perfectly
        nav1 = next(v for v in self.page1.visuals if v.visual_type == "pageNavigator")
        nav2 = next(v for v in self.page2.visuals if v.visual_type == "pageNavigator")
        self.assertEqual(nav1.x, nav2.x)
        self.assertEqual(nav1.y, nav2.y)
        self.assertEqual(nav1.width, nav2.width)
        self.assertEqual(nav1.height, nav2.height)

        # 4. Standardized KPI strip at y=142 across both pages
        kpis1 = [v for v in self.page1.visuals if v.visual_type == "cardVisual"]
        kpis2 = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        self.assertEqual(len(kpis1), 4)
        self.assertEqual(len(kpis2), 4)
        for k in kpis1 + kpis2:
            self.assertEqual(k.y, 142)
            self.assertEqual(k.height, 116)
            self.assertEqual(k.width, 444)

if __name__ == "__main__":
    unittest.main()
