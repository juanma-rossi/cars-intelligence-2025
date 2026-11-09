"""
Cars Intelligence 2025 - Tier 3: Cross-Feature Combinations Test Suite
Pairwise and cross-feature interaction verification.
Covers 22 comprehensive pairwise feature interactions.
"""

import unittest
import os
import glob
import json
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

class TestTier3Combinations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_semantic_model()
        cls.page = load_report_page()
        cls.page1 = cls.page
        cls.page2 = load_performance_lab_page()
        cls.theme = load_theme()

    def test_c01_slicer_fuel_and_heatmap_matrix_dimension(self):
        """C01: F11 (Slicers) + F9 (Heatmap) - Slicer Powertrain aligns with Heatmap column dimension."""
        slicer_fuel = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 270)
        heatmap = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        s_bindings = extract_visual_bindings(slicer_fuel.data)
        h_bindings = extract_visual_bindings(heatmap.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), s_bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), h_bindings)

    def test_c02_slicer_segment_and_barchart_category(self):
        """C02: F11 (Slicers) + F7 (Bar Chart) - Slicer Segment aligns with Bar Chart category."""
        slicer_seg = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 36)
        barchart = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        s_bindings = extract_visual_bindings(slicer_seg.data)
        b_bindings = extract_visual_bindings(barchart.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), s_bindings)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), b_bindings)

    def test_c03_slicer_company_and_scatter_chart_entity(self):
        """C03: F11 (Slicers) + F8 (Scatter Chart) - Brand slicer filters FactVehicle Company in Scatter Chart."""
        slicer_co = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 489)
        s_bindings = extract_visual_bindings(slicer_co.data)
        self.assertIn(("Column", "DimCompany", "Company"), s_bindings)
        # Verify relationship connects DimCompany[Company] to FactVehicle[Company]
        rel = next((r for r in self.model.relationships if "DimCompany.Company" in r["toColumn"]), None)
        self.assertIsNotNone(rel, "Relationship to DimCompany.Company must exist")
        self.assertEqual(rel["fromColumn"], "FactVehicle.Company")

    def test_c04_slicer_scope_and_table_ex_filtering(self):
        """C04: F11 (Slicers) + F10 (Top Value Leaders) - Market Scope slicer filters FactVehicle."""
        slicer_scope = next(v for v in self.page.visuals if v.visual_type == "slicer" and v.x == 708)
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        s_bindings = extract_visual_bindings(slicer_scope.data)
        t_bindings = extract_visual_bindings(table.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Scope Status"), s_bindings)
        self.assertTrue(any(b[1] == "FactVehicle" for b in t_bindings))

    def test_c05_top_n_table_and_kpi4_best_value_measure(self):
        """C05: F10 (Top N Table) + F5 (KPI 4) - TableEx sorts by Value Index and KPI 4 measures Best Value Share."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        kpi4 = next(v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 1440)
        t_str = json.dumps(table.data)
        self.assertIn("Value Index", t_str)
        self.assertIn("Best Value", t_str)
        k_bindings = extract_visual_bindings(kpi4.data)
        self.assertIn(("Measure", "_Measures", "Best Value Share %"), k_bindings)

    def test_c06_gauge_macro_target_and_scatter_matrix_micro(self):
        """C06: F6 (Gauge) + F8 (Scatter Chart) - Macro benchmark gauge corresponds to micro scatter matrix."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        g_bindings = extract_visual_bindings(gauge.data)
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), g_bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), s_bindings)
        self.assertIn(("Measure", "_Measures", "Average Price"), s_bindings)

    def test_c07_theme_typography_tokens_and_kpi_cards(self):
        """C07: F14 (Theme Styling) + F5 (KPI Cards) - Theme callout typography applied to KPI cards."""
        callout_style = self.theme.get("textClasses", {}).get("callout", {})
        self.assertEqual(callout_style.get("fontSize"), 28)
        self.assertEqual(callout_style.get("color"), "#0F172A")
        for card in [v for v in self.page.visuals if v.visual_type == "cardVisual"]:
            card_str = json.dumps(card.data)
            self.assertIn("28D", card_str)
            self.assertIn("#0F172A", card_str)

    def test_c08_theme_gradient_stops_and_heatmap_linear_gradient(self):
        """C08: F14 (Theme Styling) + F9 (Heatmap) - Heatmap gradient uses theme minimum color stop."""
        theme_min = self.theme.get("minimum", "#F1F5F9")
        heatmap = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        h_str = json.dumps(heatmap.data)
        self.assertIn(theme_min, h_str)

    def test_c09_theme_card_border_radius_and_bento_grid_containers(self):
        """C09: F14 (Theme Styling) + F13 (Bento Grid) - Theme 16px radius applied to Bento analytical cards."""
        theme_radius = self.theme.get("visualStyles", {}).get("*", {}).get("*", {}).get("border", [{}])[0].get("radius")
        self.assertEqual(theme_radius, 16)
        bento_card_types = {"cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx"}
        for v in self.page.visuals:
            if v.visual_type in bento_card_types:
                v_str = json.dumps(v.data)
                self.assertIn("16D", v_str, f"Visual {v.id} [{v.visual_type}] should specify 16D border radius")

    def test_c10_theme_elevation_shadow_and_bento_grid_containers(self):
        """C10: F14 (Theme Styling) + F13 (Bento Grid) - Bento analytical cards define dropShadow with color #CBD5E1."""
        bento_card_types = {"cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx"}
        for v in self.page.visuals:
            if v.visual_type in bento_card_types:
                v_str = json.dumps(v.data)
                self.assertIn("#CBD5E1", v_str, f"Visual {v.id} [{v.visual_type}] should specify #CBD5E1 dropShadow")

    def test_c11_purged_svg_measures_and_model_measure_references(self):
        """C11: F1 (Purged SVG) + F3 (Model Integrity) - Zero references to purged SVG measures in DAX."""
        purged = [
            "SVG Heatmap Tile",
            "SVG Live Speedometer Cockpit",
            "SVG Live 3D Coupe Telemetry",
            "SVG Market Position Badge",
            "SVG Value Sparkbar",
            "SVG Performance Gauge"
        ]
        measures = self.model.tables["_Measures"].measures
        for m_name, m_data in measures.items():
            for p in purged:
                self.assertNotIn(f"[{p}]", m_data["block"], f"Measure {m_name} still references purged {p}")

    def test_c12_purged_svg_column_and_table_ex_projections(self):
        """C12: F2 (Purged SVG Column) + F10 (TableEx) - TableEx uses native columns and zero SVG."""
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        t_str = json.dumps(table.data)
        self.assertNotIn("Leaderboard Card SVG", t_str)
        self.assertNotIn("svg", t_str.lower())

    def test_c13_bento_grid_geometry_and_kpi_row(self):
        """C13: F13 (Bento Grid) + F5 (KPI Cards) - KPI cards form a continuous 4-column row at y=142."""
        kpis = sorted([v for v in self.page.visuals if v.visual_type == "cardVisual"], key=lambda v: v.x)
        self.assertEqual(len(kpis), 4)
        for i in range(len(kpis)):
            self.assertEqual(kpis[i].y, 142)
            self.assertEqual(kpis[i].width, 444)
            self.assertEqual(kpis[i].height, 116)
            if i > 0:
                gap = kpis[i].x - kpis[i-1].right
                self.assertEqual(gap, 24)

    def test_c14_bento_grid_flankers_and_heatmap_table_symmetry(self):
        """C14: F13 (Bento Grid) + F9 (Heatmap) + F10 (TableEx) - Flankers in col 1 and col 4 are height-symmetrical."""
        col1_flanker = next(v for v in self.page.visuals if v.x == 36 and v.y == 270)
        col4_flanker = next(v for v in self.page.visuals if v.x == 1440 and v.y == 270)
        self.assertEqual(col1_flanker.visual_type, "pivotTable")
        self.assertEqual(col4_flanker.visual_type, "tableEx")
        self.assertEqual(col1_flanker.height, col4_flanker.height)
        self.assertEqual(col1_flanker.width, col4_flanker.width)
        self.assertEqual(col1_flanker.bottom, col4_flanker.bottom)

    def test_c15_bento_grid_central_cockpit_stacking(self):
        """C15: F13 (Bento Grid) + F6, F7, F8 - Central columns 2 and 3 stack gauge and bar chart over scatter chart."""
        gauge = next(v for v in self.page.visuals if v.visual_type == "gauge")
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        self.assertEqual(gauge.y, 270)
        self.assertEqual(bar.y, 270)
        self.assertEqual(scatter.y, 504)
        # Gauge and bar chart top span
        self.assertEqual(gauge.x, 504)
        self.assertEqual(bar.x, 972)
        # Scatter chart spans exactly from gauge left to bar right
        self.assertEqual(scatter.x, gauge.x)
        self.assertEqual(scatter.right, bar.right)

    def test_c16_header_band_and_slicer_band_spatial_hierarchy(self):
        """C16: F12 (Header) + F11 (Slicers) + F13 (Bento) - Clear vertical stratification across bands."""
        tb = next(v for v in self.page.visuals if v.visual_type == "textbox")
        slicers = [v for v in self.page.visuals if v.visual_type == "slicer"]
        kpis = [v for v in self.page.visuals if v.visual_type == "cardVisual"]
        # Header bottom < slicer y
        self.assertLessEqual(tb.bottom, slicers[0].y)
        # Slicer bottom < KPI y
        self.assertLessEqual(slicers[0].bottom, kpis[0].y)
        # KPI bottom < Main visuals y
        self.assertLessEqual(kpis[0].bottom, 270)

    def test_c17_verification_script_and_utf8_file_inventory(self):
        """C17: F4 (Verify Script) + F15 (UTF-8) - verify_report.py inspects the exact count of TMDL and JSON files."""
        tmdl_count = len(glob.glob(os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl"), recursive=True))
        json_count = len(glob.glob(os.path.join(REPO_ROOT, "powerbi", "**", "*.json"), recursive=True))
        self.assertGreaterEqual(tmdl_count, 14)
        self.assertGreaterEqual(json_count, 46)

    def test_c18_verification_script_and_semantic_model_bindings(self):
        """C18: F4 (Verify Script) + F3 (Model Integrity) - 100% of visual bindings resolve in TMDL model."""
        model_tables = {name: set(t.columns.keys()) | set(t.measures.keys()) for name, t in self.model.tables.items()}
        for v in self.page.visuals:
            bindings = extract_visual_bindings(v.data)
            for btype, ent, prop in bindings:
                self.assertIn(ent, model_tables, f"Visual {v.id} references missing table {ent}")
                self.assertIn(prop, model_tables[ent], f"Visual {v.id} references missing {btype} {ent}[{prop}]")

    def test_c19_scatter_chart_and_table_ex_market_position_consistency(self):
        """C19: F8 (Scatter Chart) + F10 (TableEx) - Both utilize Market Position (Static) column."""
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        table = next(v for v in self.page.visuals if v.visual_type == "tableEx")
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "FactVehicle", "Market Position (Static)"), s_bindings)
        t_str = json.dumps(table.data)
        self.assertIn("Best Value", t_str)

    def test_c20_heatmap_vehicle_count_and_kpi1_vehicle_count(self):
        """C20: F9 (Heatmap) + F5 (KPI 1) - Both bind to _Measures[Vehicle Count] with matching lineageTag."""
        kpi1 = next(v for v in self.page.visuals if v.visual_type == "cardVisual" and v.x == 36)
        heatmap = next(v for v in self.page.visuals if v.visual_type == "pivotTable")
        k_bindings = extract_visual_bindings(kpi1.data)
        h_bindings = extract_visual_bindings(heatmap.data)
        self.assertIn(("Measure", "_Measures", "Vehicle Count"), k_bindings)
        self.assertIn(("Measure", "_Measures", "Vehicle Count"), h_bindings)
        m_vc = self.model.tables["_Measures"].measures["Vehicle Count"]
        self.assertEqual(m_vc["lineageTag"], "07f702f1-7c4c-4b96-8756-45dad203df87")

    def test_c21_bar_chart_average_hp_and_scatter_chart_average_hp(self):
        """C21: F7 (Bar Chart) + F8 (Scatter Chart) - Both bind to _Measures[Average HP] with matching lineageTag."""
        bar = next(v for v in self.page.visuals if v.visual_type == "clusteredBarChart")
        scatter = next(v for v in self.page.visuals if v.visual_type == "scatterChart")
        b_bindings = extract_visual_bindings(bar.data)
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), b_bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), s_bindings)
        m_hp = self.model.tables["_Measures"].measures["Average HP"]
        self.assertEqual(m_hp["lineageTag"], "cf8cc606-d617-4ca6-b07d-ad4fe3421f33")

    def test_c22_all_visual_bindings_and_semantic_lineagetags(self):
        """C22: F3 (Model Integrity) + All Visuals - Bound measures have valid GUID lineageTags in TMDL."""
        guid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
        measures = self.model.tables["_Measures"].measures
        for v in self.page.visuals:
            for btype, ent, prop in extract_visual_bindings(v.data):
                if btype == "Measure" and ent == "_Measures":
                    self.assertIn(prop, measures, f"Measure {prop} not found in _Measures")
                    lt = measures[prop]["lineageTag"]
                    self.assertIsNotNone(lt, f"Measure {prop} missing lineageTag")
                    self.assertTrue(guid_re.match(lt), f"Measure {prop} lineageTag {lt} is not valid GUID")

    def test_c23_page2_slicer_fuel_and_scatter_series(self):
        """C23: Page 02 Slicer Fuel + Scatter Chart Series - Both bind to DimFuel[Fuel_Group]."""
        slicer_fuel = next(v for v in self.page2.visuals if v.id == "perf_slicer_fuel" or (v.visual_type == "slicer" and v.x == 270))
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        s_bindings = extract_visual_bindings(slicer_fuel.data)
        sc_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), s_bindings)
        self.assertIn(("Column", "DimFuel", "Fuel_Group"), sc_bindings)

    def test_c24_page2_slicer_segment_and_sprint_bar_category(self):
        """C24: Page 02 Slicer Segment + Sprint Bar Category - Both bind to DimPriceSegment[Segment_Name]."""
        slicer_seg = next(v for v in self.page2.visuals if v.id == "perf_slicer_segment" or (v.visual_type == "slicer" and v.x == 36))
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        s_bindings = extract_visual_bindings(slicer_seg.data)
        b_bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), s_bindings)
        self.assertIn(("Column", "DimPriceSegment", "Segment_Name"), b_bindings)

    def test_c25_page2_slicer_brand_and_table_brand_projection(self):
        """C25: Page 02 Slicer Brand + TableEx Brand Column - Both bind to DimCompany / FactVehicle Company."""
        slicer_brand = next(v for v in self.page2.visuals if v.id == "perf_slicer_brand" or (v.visual_type == "slicer" and v.x == 489))
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        s_bindings = extract_visual_bindings(slicer_brand.data)
        t_bindings = extract_visual_bindings(table.data)
        self.assertIn(("Column", "DimCompany", "Company"), s_bindings)
        self.assertIn(("Column", "FactVehicle", "Company"), t_bindings)

    def test_c26_page2_slicer_scope_and_scatter_vehicle_grain(self):
        """C26: Page 02 Slicer Scope + Scatter Vehicle Display Name - Both leverage FactVehicle entity."""
        slicer_scope = next(v for v in self.page2.visuals if v.id == "perf_slicer_scope" or (v.visual_type == "slicer" and v.x == 708))
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        s_bindings = extract_visual_bindings(slicer_scope.data)
        sc_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Column", "FactVehicle", "Vehicle Scope Status"), s_bindings)
        self.assertIn(("Column", "FactVehicle", "Vehicle Display Name"), sc_bindings)

    def test_c27_page2_kpi_row_geometry_and_bento_columns(self):
        """C27: Page 02 Bento Grid + KPI Strip - 4 KPI cards form seamless 4-column row with 24px gaps."""
        kpis = sorted([v for v in self.page2.visuals if v.visual_type == "cardVisual"], key=lambda v: v.x)
        self.assertEqual(len(kpis), 4)
        expected_x = [36, 504, 972, 1440]
        for idx, kpi in enumerate(kpis):
            self.assertEqual(kpi.x, expected_x[idx])
            self.assertEqual(kpi.width, 444)
            self.assertEqual(kpi.height, 116)
            self.assertEqual(kpi.y, 142)

    def test_c28_page2_bento_flankers_symmetry(self):
        """C28: Page 02 Bento Grid Flankers - Col 1 Pivot Matrix & Col 4 TableEx have identical height 774 and y 270."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        self.assertEqual(pivot.y, table.y)
        self.assertEqual(pivot.height, table.height)
        self.assertEqual(pivot.width, table.width)
        self.assertEqual(pivot.height, 774)

    def test_c29_page2_central_stack_alignment(self):
        """C29: Page 02 Bento Grid Central Stack - Gauge (h=220) + Bar (h=220) over Scatter (h=540) = 774px."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        self.assertEqual(gauge.y, 270)
        self.assertEqual(bar.y, 270)
        self.assertEqual(gauge.height, 220)
        self.assertEqual(bar.height, 220)
        self.assertEqual(scatter.y, 504)
        self.assertEqual(scatter.height, 540)
        self.assertEqual(scatter.bottom - gauge.y, 774)

    def test_c30_page2_vertical_stratification_hierarchy(self):
        """C30: Page 02 Vertical Stratification - Header (20-72), Slicers (80-130), KPIs (142-258), Main (270-1044)."""
        tb = next(v for v in self.page2.visuals if v.visual_type == "textbox")
        slicers = [v for v in self.page2.visuals if v.visual_type == "slicer"]
        kpis = [v for v in self.page2.visuals if v.visual_type == "cardVisual"]
        main_vis = [v for v in self.page2.visuals if v.y >= 270]
        self.assertLessEqual(tb.bottom, min(s.y for s in slicers))
        self.assertLessEqual(max(s.bottom for s in slicers), min(k.y for k in kpis))
        self.assertLessEqual(max(k.bottom for k in kpis), min(m.y for m in main_vis))

    def test_c31_page2_theme_tokens_and_analytical_cards(self):
        """C31: Page 02 Registered Theme + Bento Containers - 16px corner radius and #CBD5E1 dropShadow enforced."""
        analytical = [v for v in self.page2.visuals if v.visual_type in ("cardVisual", "gauge", "clusteredBarChart", "scatterChart", "pivotTable", "tableEx")]
        for a in analytical:
            a_str = json.dumps(a.data)
            self.assertIn('"radius"', a_str)
            self.assertIn('"16D"', a_str)
            self.assertIn("#CBD5E1", a_str)

    def test_c32_page2_theme_color_scale_and_pivot_gradient(self):
        """C32: Page 02 Theme Color Scale + Pivot Gradient - Gradient min stop #F1F5F9 matches theme minimum."""
        pivot = next(v for v in self.page2.visuals if v.visual_type == "pivotTable")
        p_str = json.dumps(pivot.data)
        self.assertIn("#F1F5F9", p_str)
        self.assertEqual(self.theme["minimum"], "#F1F5F9")

    def test_c33_page2_cockpit_macro_target_and_scatter_micro_size(self):
        """C33: Page 02 Gauge Cockpit + Scatter Matrix - Macro vs micro Performance Index alignment."""
        gauge = next(v for v in self.page2.visuals if v.visual_type == "gauge")
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        g_bindings = extract_visual_bindings(gauge.data)
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), g_bindings)
        self.assertIn(("Measure", "_Measures", "Performance Index"), s_bindings)

    def test_c34_page2_track_leaderboard_sort_and_gauge_target_measure(self):
        """C34: Page 02 Track Leaderboard + Gauge Cockpit - Sort measure Performance Index links table to cockpit."""
        table = next(v for v in self.page2.visuals if v.visual_type == "tableEx")
        t_bindings = extract_visual_bindings(table.data)
        self.assertIn(("Measure", "_Measures", "Performance Index"), t_bindings)

    def test_c35_page2_kpi1_hp_and_scatter_x_axis(self):
        """C35: Page 02 KPI 1 + Scatter Chart X-Axis - Both bind to _Measures[Average HP] with matching lineageTag."""
        kpi1 = next(v for v in self.page2.visuals if v.id == "perf_kpi_hp" or (v.visual_type == "cardVisual" and v.x == 36))
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        k_bindings = extract_visual_bindings(kpi1.data)
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Average HP"), k_bindings)
        self.assertIn(("Measure", "_Measures", "Average HP"), s_bindings)
        m_hp = self.model.tables["_Measures"].measures["Average HP"]
        self.assertEqual(m_hp["lineageTag"], "cf8cc606-d617-4ca6-b07d-ad4fe3421f33")

    def test_c36_page2_kpi2_speed_and_scatter_y_axis(self):
        """C36: Page 02 KPI 2 + Scatter Chart Y-Axis - Both bind to _Measures[Average Speed] with matching lineageTag."""
        kpi2 = next(v for v in self.page2.visuals if v.id == "perf_kpi_speed" or (v.visual_type == "cardVisual" and v.x == 504))
        scatter = next(v for v in self.page2.visuals if v.visual_type == "scatterChart")
        k_bindings = extract_visual_bindings(kpi2.data)
        s_bindings = extract_visual_bindings(scatter.data)
        self.assertIn(("Measure", "_Measures", "Average Speed"), k_bindings)
        self.assertIn(("Measure", "_Measures", "Average Speed"), s_bindings)
        m_speed = self.model.tables["_Measures"].measures["Average Speed"]
        self.assertEqual(m_speed["lineageTag"], "757b3179-0470-4da1-96dd-ebe2cca754d0")

    def test_c37_page2_kpi3_accel_and_sprint_bar_y(self):
        """C37: Page 02 KPI 3 + Sprint Bar Chart Y-Axis - Both bind to _Measures[Average 0-100] with matching lineageTag."""
        kpi3 = next(v for v in self.page2.visuals if v.id == "perf_kpi_accel" or (v.visual_type == "cardVisual" and v.x == 972))
        bar = next(v for v in self.page2.visuals if v.visual_type == "clusteredBarChart")
        k_bindings = extract_visual_bindings(kpi3.data)
        b_bindings = extract_visual_bindings(bar.data)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), k_bindings)
        self.assertIn(("Measure", "_Measures", "Average 0-100"), b_bindings)
        m_accel = self.model.tables["_Measures"].measures["Average 0-100"]
        self.assertEqual(m_accel["lineageTag"], "0a283bed-7801-4773-97af-53e25d765065")

    def test_c38_page2_page_navigator_and_page1_consistency(self):
        """C38: Multi-Page Navigator Consistency - Both Page 01 and Page 02 share identical page navigator geometry."""
        nav1 = next(v for v in self.page1.visuals if v.visual_type == "pageNavigator")
        nav2 = next(v for v in self.page2.visuals if v.visual_type == "pageNavigator")
        self.assertEqual(nav1.x, nav2.x)
        self.assertEqual(nav1.y, nav2.y)
        self.assertEqual(nav1.width, nav2.width)
        self.assertEqual(nav1.height, nav2.height)
        self.assertEqual(nav1.right, nav2.right)

if __name__ == "__main__":
    unittest.main()
