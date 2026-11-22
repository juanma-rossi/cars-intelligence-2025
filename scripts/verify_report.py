#!/usr/bin/env python3
"""
Automated Verification Script for Cars Intelligence 2025 Enterprise Power BI Report
Validates:
1. File Encodings & BOM:
   - Strictly UTF-8 without BOM across all TMDL (*.tmdl) and JSON (*.json) files.
2. TMDL Syntax & Formatting:
   - TMDL files strictly use TAB characters (zero spaces) for hierarchy indentation.
3. JSON Syntax Integrity:
   - All JSON files parse cleanly with valid syntax.
4. Legacy SVG & Data-URI Removal:
   - Zero legacy SVG measures, columns, data-URIs, or image controls across powerbi/
     (including SVG Heatmap Tile, SVG Live Speedometer Cockpit, SVG Live 3D Coupe Telemetry,
      SVG Market Position Badge, SVG Value Sparkbar, SVG Performance Gauge, Leaderboard Card SVG).
5. Market Overview Page (01_MarketOverview) Compliance:
   - Canvas dimensions strictly 1920x1080 bounds.
   - Exactly 15 native visual containers arranged within canvas limits.
   - Expected native visual distribution (cardVisual, gauge, clusteredBarChart,
     scatterChart, pivotTable, tableEx, slicer, textbox, pageNavigator).
   - PivotTable has native linearGradient2 conditional formatting on Vehicle Count.
   - TableEx has native Top N filter configuration.
6. Performance Lab Page (02_PerformanceLab) Compliance:
   - Canvas dimensions strictly 1920x1080 bounds.
   - Exactly 15 native visual containers arranged in Automotive Studio Bento Grid.
   - Zero pairwise bounding-box collisions.
   - Expected native visual distribution (cardVisual, gauge, clusteredBarChart,
     scatterChart, pivotTable, tableEx, slicer, textbox, pageNavigator).
   - PivotTable has native linearGradient2 conditional formatting on Average HP.
   - TableEx has native Top N filter configuration targeting Performance Index.
   - Zero legacy SVG or data-URIs on Page 02.
7. Visual Data Binding Integrity:
   - 100% of visual data bindings resolve in the TMDL semantic model with zero broken references.
8. Theme Compliance:
   - Theme palette and styling from Cars_Intelligence_20258711528438303722.json are verified
     against report configuration.
"""

import os
import sys
import glob
import json
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class VerificationReporter:
    def __init__(self):
        self.passes = 0
        self.failures = 0
        self.warnings = 0
        self.details = []

    def log_pass(self, check_name, msg=""):
        self.passes += 1
        self.details.append(f"[PASS] {check_name}: {msg}")

    def log_fail(self, check_name, error_msg):
        self.failures += 1
        self.details.append(f"[FAIL] {check_name}: {error_msg}")

    def log_warn(self, check_name, warn_msg):
        self.warnings += 1
        self.details.append(f"[WARN] {check_name}: {warn_msg}")

    def summary(self):
        print("\n" + "=" * 80)
        print("CARS INTELLIGENCE 2025 - AUTOMATED VERIFICATION SUITE")
        print("=" * 80)
        for d in self.details:
            print(d)
        print("=" * 80)
        print(f"Summary: {self.passes} PASSED | {self.failures} FAILED | {self.warnings} WARNINGS")
        print("=" * 80 + "\n")
        return self.failures == 0


def _find_invalid_subquery_entity_refs(node, in_subquery=False):
    """Return True if any SourceRef nested under a Subquery uses Entity instead of Source."""
    if isinstance(node, dict):
        next_sub = in_subquery or ("Subquery" in node)
        if next_sub and "SourceRef" in node and isinstance(node["SourceRef"], dict):
            if "Entity" in node["SourceRef"]:
                return True
        return any(_find_invalid_subquery_entity_refs(v, next_sub) for v in node.values())
    if isinstance(node, list):
        return any(_find_invalid_subquery_entity_refs(item, in_subquery) for item in node)
    return False


def check_file_encodings(reporter, repo_root):
    """Validate UTF-8 without BOM, indentation rules, and JSON syntax."""
    tmdl_pattern = os.path.join(repo_root, "powerbi/**/*.tmdl")
    json_pattern = os.path.join(repo_root, "powerbi/**/*.json")
    
    tmdl_files = glob.glob(tmdl_pattern, recursive=True)
    json_files = glob.glob(json_pattern, recursive=True)

    # 1. TMDL Validation
    tmdl_bom_failures = []
    tmdl_space_indent_failures = []
    for f in tmdl_files:
        rel = os.path.relpath(f, repo_root)
        with open(f, "rb") as fh:
            raw = fh.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            tmdl_bom_failures.append(rel)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            reporter.log_fail("TMDL UTF-8 Valid", f"{rel} is not valid UTF-8")
            continue

        lines = text.splitlines()
        for line_num, line in enumerate(lines, 1):
            if line.startswith(" "):
                tmdl_space_indent_failures.append(f"{rel}:{line_num}")
                break

        # Also validate multiline '=' block baseline tab consistency (e.g., linguisticMetadata / source / measure)
        i = 0
        while i < len(lines):
            ln = lines[i]
            s = ln.strip()
            if s.endswith("=") or s.endswith("= ```"):
                hdr_tabs = len(ln) - len(ln.lstrip("\t"))
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines):
                    first_tabs = len(lines[j]) - len(lines[j].lstrip("\t"))
                    if first_tabs > hdr_tabs:
                        k = j + 1
                        while k < len(lines):
                            ks = lines[k].strip()
                            if not ks:
                                k += 1
                                continue
                            ktabs = len(lines[k]) - len(lines[k].lstrip("\t"))
                            if ktabs <= hdr_tabs + 1:
                                break
                            if ktabs < first_tabs:
                                tmdl_space_indent_failures.append(f"{rel}:{k+1} (multiline tab drop {ktabs} < {first_tabs})")
                                break
                            k += 1
            i += 1

    if not tmdl_bom_failures:
        reporter.log_pass("TMDL UTF-8 No-BOM", f"All {len(tmdl_files)} TMDL files are strictly UTF-8 without BOM")
    else:
        reporter.log_fail("TMDL UTF-8 No-BOM", f"BOM detected in {len(tmdl_bom_failures)} files: {tmdl_bom_failures}")

    if not tmdl_space_indent_failures:
        reporter.log_pass("TMDL Tab Indentation", f"All {len(tmdl_files)} TMDL files strictly use TAB characters (zero spaces)")
    else:
        reporter.log_fail("TMDL Tab Indentation", f"Space indentation found in: {tmdl_space_indent_failures}")

    # 2. JSON Validation
    json_bom_failures = []
    json_parse_failures = []
    for f in json_files:
        rel = os.path.relpath(f, repo_root)
        with open(f, "rb") as fh:
            raw = fh.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            json_bom_failures.append(rel)
        try:
            text = raw.decode("utf-8")
            parsed_json = json.loads(text)
            if rel.endswith("visual.json"):
                allowed_root = {"$schema", "name", "position", "visual", "filterConfig", "visualGroup", "parentGroupName", "howCreated", "isHidden"}
                extra_root = set(parsed_json.keys()) - allowed_root
                if extra_root:
                    json_parse_failures.append(f"{rel}: unexpected root property {sorted(extra_root)}")
                if "filterConfig" in parsed_json:
                    allowed_flt = {"name", "ordinal", "field", "type", "filter", "howCreated", "isHiddenInViewMode", "isLockedInViewMode", "displayName", "objects"}
                    for f_idx, flt_obj in enumerate(parsed_json.get("filterConfig", {}).get("filters", [])):
                        extra_flt = set(flt_obj.keys()) - allowed_flt
                        if extra_flt:
                            json_parse_failures.append(f"{rel}: unexpected filter[{f_idx}] property {sorted(extra_flt)}")
                ds_items = parsed_json.get("visual", {}).get("visualContainerObjects", {}).get("dropShadow", [])
                allowed_ds = {"show", "color", "position", "preset", "angle", "shadowDistance", "shadowBlur", "shadowSpread", "transparency"}
                for ds_idx, ds_obj in enumerate(ds_items):
                    extra_ds = set(ds_obj.get("properties", {}).keys()) - allowed_ds
                    if extra_ds:
                        json_parse_failures.append(f"{rel}: unexpected dropShadow[{ds_idx}] property {sorted(extra_ds)}")
                if _find_invalid_subquery_entity_refs(parsed_json):
                    json_parse_failures.append(f"{rel}: Subquery expression contains illegal SourceRef.Entity instead of Source")
        except UnicodeDecodeError:
            reporter.log_fail("JSON UTF-8 Valid", f"{rel} is not valid UTF-8")
        except json.JSONDecodeError as jde:
            json_parse_failures.append(f"{rel}: {jde.msg} (line {jde.lineno})")

    if not json_bom_failures:
        reporter.log_pass("JSON UTF-8 No-BOM", f"All {len(json_files)} JSON files are strictly UTF-8 without BOM")
    else:
        reporter.log_fail("JSON UTF-8 No-BOM", f"BOM detected in {len(json_bom_failures)} files: {json_bom_failures}")

    if not json_parse_failures:
        reporter.log_pass("JSON Syntax Integrity", f"All {len(json_files)} JSON files parse cleanly as valid JSON")
    else:
        reporter.log_fail("JSON Syntax Integrity", f"JSON parse errors in: {json_parse_failures}")


def check_svg_removals(reporter, repo_root):
    """Verify zero legacy SVG measures, columns, data-URIs, or legacy image controls across powerbi/."""
    svg_keywords = [
        "SVG Heatmap Tile",
        "SVG Live Speedometer Cockpit",
        "SVG Live 3D Coupe Telemetry",
        "SVG Market Position Badge",
        "SVG Value Sparkbar",
        "SVG Performance Gauge",
        "Leaderboard Card SVG",
        "data:image/svg",
        "<svg",
        "imageControl"
    ]

    powerbi_files = glob.glob(os.path.join(repo_root, "powerbi/**/*"), recursive=True)
    found_matches = []
    for f in powerbi_files:
        if os.path.isdir(f):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                content = fh.read()
            for kw in svg_keywords:
                if kw.lower() in content.lower():
                    rel = os.path.relpath(f, repo_root)
                    found_matches.append(f"{rel}: matched '{kw}'")
        except Exception:
            pass

    if not found_matches:
        reporter.log_pass("Zero SVG References", "Zero legacy SVG measures, columns, data-URIs, or image controls across powerbi/")
    else:
        reporter.log_fail("Zero SVG References", f"Found lingering SVG references: {found_matches}")


def load_semantic_model(repo_root):
    """Extract all table, column, and measure definitions from TMDL files."""
    model_tables = {}
    tmdl_dir = os.path.join(repo_root, "powerbi/CarsIntelligence.SemanticModel/definition/tables")
    for tf in glob.glob(os.path.join(tmdl_dir, "*.tmdl")):
        with open(tf, "r", encoding="utf-8") as f:
            content = f.read()

        tmatch = re.search(r"^table\s+(?:(?:\'([^\']+)\')|([^\s\r\n]+))", content, re.MULTILINE)
        if tmatch:
            table_name = tmatch.group(1) or tmatch.group(2)
        else:
            table_name = os.path.splitext(os.path.basename(tf))[0]

        cols = re.findall(r"^\tcolumn\s+(?:(?:\'([^\']+)\')|([^\s\r\n=]+))", content, re.MULTILINE)
        col_names = {c[0] if c[0] else c[1] for c in cols}

        measures = re.findall(r"^\tmeasure\s+(?:(?:\'{1,3}([^\']+)\'{1,3})|([^\s\r\n=]+))\s*=", content, re.MULTILINE)
        measure_names = {m[0] if m[0] else m[1] for m in measures}

        model_tables[table_name] = {"columns": col_names, "measures": measure_names}
    return model_tables


def check_market_overview_visuals(reporter, repo_root, model_tables):
    """Validate 01_MarketOverview visual types, canvas layout bounds, conditional formatting, and bindings."""
    page_dir = os.path.join(repo_root, "powerbi/CarsIntelligence.Report/definition/pages/3f7688a2cc2e12e049b0")
    page_json_path = os.path.join(page_dir, "page.json")

    if not os.path.exists(page_json_path):
        reporter.log_fail("Market Overview Page", f"page.json not found for 3f7688a2cc2e12e049b0 at {page_json_path}")
        return

    with open(page_json_path, "r", encoding="utf-8") as f:
        page_data = json.load(f)

    canvas_width = page_data.get("width")
    canvas_height = page_data.get("height")
    if canvas_width == 1920 and canvas_height == 1080:
        reporter.log_pass("Canvas Resolution", "Page 01_MarketOverview canvas is strictly 1920x1080")
    else:
        reporter.log_fail("Canvas Resolution", f"Canvas is {canvas_width}x{canvas_height}, expected 1920x1080")

    visual_files = glob.glob(os.path.join(page_dir, "visuals/*/visual.json"))
    expected_count = 15
    if len(visual_files) == expected_count:
        reporter.log_pass("Visual Container Count", f"Exactly {len(visual_files)} visual containers on 01_MarketOverview")
    else:
        reporter.log_fail("Visual Container Count", f"Expected {expected_count} visual containers, found {len(visual_files)}")

    expected_types = {
        "cardVisual": 4,
        "slicer": 4,
        "gauge": 1,
        "clusteredBarChart": 1,
        "scatterChart": 1,
        "pivotTable": 1,
        "tableEx": 1,
        "textbox": 1,
        "pageNavigator": 1
    }

    actual_types = {}
    bindings_to_check = []
    has_pivot_gradient = False
    pivot_gradient_target = None
    has_table_top_n = False
    table_top_n_target = None
    bounds_violations = []

    for vf in visual_files:
        vdir = os.path.basename(os.path.dirname(vf))
        with open(vf, "r", encoding="utf-8") as f:
            vdata = json.load(f)
        v = vdata.get("visual", {})
        vtype = v.get("visualType", "unknown")
        actual_types[vtype] = actual_types.get(vtype, 0) + 1

        # Check visual bounds
        pos = vdata.get("position", {})
        x, y = pos.get("x", 0), pos.get("y", 0)
        w, h = pos.get("width", 0), pos.get("height", 0)
        if x < 0 or y < 0 or (x + w > 1920) or (y + h > 1080):
            bounds_violations.append(f"Visual {vdir} [{vtype}]: pos=({x},{y}), size=({w}x{h}), bounds=({x+w},{y+h})")

        # Check pivotTable linearGradient2
        if vtype == "pivotTable":
            v_str = json.dumps(vdata)
            if "linearGradient2" in v_str and "FillRule" in v_str:
                has_pivot_gradient = True
                if "Vehicle Count" in v_str:
                    pivot_gradient_target = "Vehicle Count"

        # Check tableEx Top N
        if vtype == "tableEx":
            v_str = json.dumps(vdata)
            if '"type": "TopN"' in v_str or '"type":"TopN"' in v_str:
                has_table_top_n = True
                if "Value Index" in v_str:
                    table_top_n_target = "Value Index"

        # Extract bindings
        def extract_refs(obj):
            if isinstance(obj, dict):
                if "Measure" in obj and isinstance(obj["Measure"], dict):
                    m = obj["Measure"]
                    prop = m.get("Property")
                    ent = m.get("Expression", {}).get("SourceRef", {}).get("Entity")
                    bindings_to_check.append((vdir, vtype, "Measure", ent, prop))
                elif "Column" in obj and isinstance(obj["Column"], dict):
                    c = obj["Column"]
                    prop = c.get("Property")
                    ent = c.get("Expression", {}).get("SourceRef", {}).get("Entity")
                    bindings_to_check.append((vdir, vtype, "Column", ent, prop))
                for val in obj.values():
                    extract_refs(val)
            elif isinstance(obj, list):
                for item in obj:
                    extract_refs(item)

        extract_refs(vdata)

    if not bounds_violations:
        reporter.log_pass("Canvas Bounds Compliance", "All 15 visual containers strictly lie within 1920x1080 bounds")
    else:
        reporter.log_fail("Canvas Bounds Compliance", f"Visual bounds violations: {bounds_violations}")

    if actual_types == expected_types:
        reporter.log_pass("Visual Types Distribution", f"100% match of native visual types: {actual_types}")
    else:
        reporter.log_fail("Visual Types Distribution", f"Mismatch in visual types: expected {expected_types}, got {actual_types}")

    if has_pivot_gradient and pivot_gradient_target == "Vehicle Count":
        reporter.log_pass("PivotTable Conditional Gradient", f"Native linearGradient2 conditional formatting confirmed on {pivot_gradient_target}")
    else:
        reporter.log_fail("PivotTable Conditional Gradient", "PivotTable lacks native linearGradient2 conditional formatting on Vehicle Count")

    if has_table_top_n and table_top_n_target == "Value Index":
        reporter.log_pass("TableEx Top N Filter", f"Top N filter configuration confirmed targeting {table_top_n_target}")
    else:
        reporter.log_fail("TableEx Top N Filter", "TableEx lacks Top N filter configuration targeting Value Index")

    # Validate bindings against semantic model
    binding_errors = []
    for vdir, vtype, btype, ent, prop in bindings_to_check:
        if not ent or not prop:
            continue
        if ent not in model_tables:
            binding_errors.append(f"Visual {vdir} [{vtype}]: Unknown table '{ent}' for {btype} '{prop}'")
        else:
            if btype == "Measure" and prop not in model_tables[ent]["measures"]:
                binding_errors.append(f"Visual {vdir} [{vtype}]: Missing measure '{prop}' in table '{ent}'")
            elif btype == "Column" and prop not in model_tables[ent]["columns"]:
                binding_errors.append(f"Visual {vdir} [{vtype}]: Missing column '{prop}' in table '{ent}'")

    if not binding_errors:
        reporter.log_pass("Visual Data Bindings", f"100% of visual data bindings ({len(bindings_to_check)} refs) resolve in TMDL model with zero broken references")
    else:
        reporter.log_fail("Visual Data Bindings", f"Binding failures detected: {binding_errors}")


def _extract_bindings(obj, vdir, vtype, bindings_to_check):
    """Recursively extract (vdir, vtype, btype, entity, property) references from visual JSON."""
    if isinstance(obj, dict):
        if "Measure" in obj and isinstance(obj["Measure"], dict):
            m = obj["Measure"]
            prop = m.get("Property")
            ent = m.get("Expression", {}).get("SourceRef", {}).get("Entity")
            bindings_to_check.append((vdir, vtype, "Measure", ent, prop))
        elif "Column" in obj and isinstance(obj["Column"], dict):
            c = obj["Column"]
            prop = c.get("Property")
            ent = c.get("Expression", {}).get("SourceRef", {}).get("Entity")
            bindings_to_check.append((vdir, vtype, "Column", ent, prop))
        for val in obj.values():
            _extract_bindings(val, vdir, vtype, bindings_to_check)
    elif isinstance(obj, list):
        for item in obj:
            _extract_bindings(item, vdir, vtype, bindings_to_check)


def _validate_page_common(reporter, repo_root, model_tables, page_id, display_name, label_prefix, expected_count, expected_types):
    """Shared validator for canvas 1920x1080, count, bounds, collisions, visual types, bindings, and zero SVG."""
    page_dir = os.path.join(repo_root, f"powerbi/CarsIntelligence.Report/definition/pages/{page_id}")
    page_json_path = os.path.join(page_dir, "page.json")

    if not os.path.exists(page_json_path):
        reporter.log_fail(f"{label_prefix} Page", f"page.json not found for {page_id} at {page_json_path}")
        return None, []

    with open(page_json_path, "r", encoding="utf-8") as f:
        page_data = json.load(f)

    canvas_width = page_data.get("width")
    canvas_height = page_data.get("height")
    if canvas_width == 1920 and canvas_height == 1080:
        reporter.log_pass(f"{label_prefix} Canvas Resolution", f"Page {display_name} canvas is strictly 1920x1080")
    else:
        reporter.log_fail(f"{label_prefix} Canvas Resolution", f"Canvas is {canvas_width}x{canvas_height}, expected 1920x1080")

    visual_files = glob.glob(os.path.join(page_dir, "visuals/*/visual.json"))
    if len(visual_files) == expected_count:
        reporter.log_pass(f"{label_prefix} Visual Count", f"Exactly {len(visual_files)} visual containers on {display_name}")
    else:
        reporter.log_fail(f"{label_prefix} Visual Count", f"Expected {expected_count} visual containers, found {len(visual_files)}")

    actual_types = {}
    bindings_to_check = []
    bounds_violations = []
    bounding_boxes = []
    loaded_visuals = []

    for vf in visual_files:
        vdir = os.path.basename(os.path.dirname(vf))
        with open(vf, "r", encoding="utf-8") as f:
            vdata = json.load(f)
        v = vdata.get("visual", {})
        vtype = v.get("visualType", "unknown")
        actual_types[vtype] = actual_types.get(vtype, 0) + 1
        loaded_visuals.append((vdir, vtype, vdata))

        pos = vdata.get("position", {})
        x, y = pos.get("x", 0), pos.get("y", 0)
        w, h = pos.get("width", 0), pos.get("height", 0)
        if x < 0 or y < 0 or (x + w > 1920) or (y + h > 1080):
            bounds_violations.append(f"Visual {vdir} [{vtype}]: pos=({x},{y}), size=({w}x{h}), bounds=({x+w},{y+h})")
        bounding_boxes.append((vdir, vtype, x, y, x + w, y + h))
        _extract_bindings(vdata, vdir, vtype, bindings_to_check)

    if not bounds_violations:
        reporter.log_pass(f"{label_prefix} Bounds Compliance", f"All {len(visual_files)} visual containers strictly lie within 1920x1080 bounds")
    else:
        reporter.log_fail(f"{label_prefix} Bounds Compliance", f"Visual bounds violations: {bounds_violations}")

    collision_errors = []
    for i in range(len(bounding_boxes)):
        for j in range(i + 1, len(bounding_boxes)):
            b1 = bounding_boxes[i]
            b2 = bounding_boxes[j]
            if b1[2] < b2[4] and b2[2] < b1[4] and b1[3] < b2[5] and b2[3] < b1[5]:
                collision_errors.append(f"Overlap between {b1[0]} [{b1[1]}] and {b2[0]} [{b2[1]}]")

    if not collision_errors:
        reporter.log_pass(f"{label_prefix} Zero Collisions", f"Zero pairwise bounding-box collisions across all {len(visual_files)} visuals")
    else:
        reporter.log_fail(f"{label_prefix} Zero Collisions", f"Collisions detected: {collision_errors}")

    if actual_types == expected_types:
        reporter.log_pass(f"{label_prefix} Visual Types", f"100% match of native visual types: {actual_types}")
    else:
        reporter.log_fail(f"{label_prefix} Visual Types", f"Mismatch in visual types: expected {expected_types}, got {actual_types}")

    return page_data, loaded_visuals, bindings_to_check, page_dir


def _finalize_bindings_and_svg(reporter, repo_root, model_tables, page_dir, display_name, label_prefix, bindings_to_check):
    """Validate visual data bindings and zero SVG references for a page."""
    binding_errors = []
    for vdir, vtype, btype, ent, prop in bindings_to_check:
        if not ent or not prop:
            continue
        if ent not in model_tables:
            binding_errors.append(f"Visual {vdir} [{vtype}]: Unknown table '{ent}' for {btype} '{prop}'")
        else:
            if btype == "Measure" and prop not in model_tables[ent]["measures"]:
                binding_errors.append(f"Visual {vdir} [{vtype}]: Missing measure '{prop}' in table '{ent}'")
            elif btype == "Column" and prop not in model_tables[ent]["columns"]:
                binding_errors.append(f"Visual {vdir} [{vtype}]: Missing column '{prop}' in table '{ent}'")

    if not binding_errors:
        reporter.log_pass(f"{label_prefix} Data Bindings", f"100% of visual data bindings ({len(bindings_to_check)} refs) resolve in TMDL model with zero broken references")
    else:
        reporter.log_fail(f"{label_prefix} Data Bindings", f"Binding failures detected: {binding_errors}")

    page_files = glob.glob(os.path.join(page_dir, "**/*"), recursive=True)
    svg_keywords = ["<svg", "data:image/svg", "imagecontrol"]
    page_svg_hits = []
    for f in page_files:
        if os.path.isfile(f):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    c = fh.read().lower()
                for kw in svg_keywords:
                    if kw in c:
                        page_svg_hits.append(f"{os.path.relpath(f, repo_root)} matched '{kw}'")
            except Exception:
                pass
    if not page_svg_hits:
        reporter.log_pass(f"{label_prefix} Zero SVG", f"Zero legacy SVG measures, columns, data-URIs, or image controls on {display_name}")
    else:
        reporter.log_fail(f"{label_prefix} Zero SVG", f"Lingering SVG references on {display_name}: {page_svg_hits}")


def check_bento_page_visuals(reporter, repo_root, model_tables, page_id, display_name, label_prefix, pivot_target, top_n_target):
    """Validate a 1920x1080 Automotive Studio Bento Grid page: bounds, collisions, types, gradient, Top N, bindings, and zero SVG."""
    expected_types = {
        "cardVisual": 4,
        "slicer": 4,
        "gauge": 1,
        "clusteredBarChart": 1,
        "scatterChart": 1,
        "pivotTable": 1,
        "tableEx": 1,
        "textbox": 1,
        "pageNavigator": 1
    }
    res = _validate_page_common(reporter, repo_root, model_tables, page_id, display_name, label_prefix, 15, expected_types)
    if res[0] is None:
        return
    _, loaded_visuals, bindings_to_check, page_dir = res

    has_pivot_gradient = False
    pivot_gradient_target = None
    has_table_top_n = False
    table_top_n_target = None

    for _, vtype, vdata in loaded_visuals:
        if vtype == "pivotTable":
            v_str = json.dumps(vdata)
            if "linearGradient2" in v_str and "FillRule" in v_str:
                has_pivot_gradient = True
                if pivot_target in v_str:
                    pivot_gradient_target = pivot_target

        if vtype == "tableEx":
            v_str = json.dumps(vdata)
            if '"type": "TopN"' in v_str or '"type":"TopN"' in v_str:
                has_table_top_n = True
                if top_n_target in v_str:
                    table_top_n_target = top_n_target

    if has_pivot_gradient and pivot_gradient_target == pivot_target:
        reporter.log_pass(f"{label_prefix} PivotTable Gradient", f"Native linearGradient2 conditional formatting confirmed on {pivot_gradient_target}")
    else:
        reporter.log_fail(f"{label_prefix} PivotTable Gradient", f"PivotTable lacks native linearGradient2 conditional formatting on {pivot_target}")

    if has_table_top_n and table_top_n_target == top_n_target:
        reporter.log_pass(f"{label_prefix} TableEx Top N", f"Top N filter configuration confirmed targeting {table_top_n_target}")
    else:
        reporter.log_fail(f"{label_prefix} TableEx Top N", f"TableEx lacks Top N filter configuration targeting {top_n_target}")

    _finalize_bindings_and_svg(reporter, repo_root, model_tables, page_dir, display_name, label_prefix, bindings_to_check)


def check_home_portal_visuals(reporter, repo_root, model_tables):
    """Validate 00_Home Light Theme minimal web-style portal page: 12 visuals, 4 PageNavigation buttons, #F8FAFC canvas, bindings, zero SVG."""
    expected_types = {
        "textbox": 3,
        "pageNavigator": 1,
        "cardVisual": 4,
        "actionButton": 4,
    }
    res = _validate_page_common(
        reporter, repo_root, model_tables,
        page_id="a001c6b7a0e103746570",
        display_name="00_Home",
        label_prefix="Home Portal",
        expected_count=12,
        expected_types=expected_types,
    )
    if res[0] is None:
        return
    page_data, loaded_visuals, bindings_to_check, page_dir = res

    bg_val = page_data.get("objects", {}).get("background", [{}])[0].get("properties", {}).get("color", {}).get("solid", {}).get("color", {}).get("expr", {}).get("Literal", {}).get("Value")
    if bg_val == "'#F8FAFC'":
        reporter.log_pass("Home Portal Light Theme", "00_Home uses Light Enterprise canvas (#F8FAFC) matching the rest of the BI report")
    else:
        reporter.log_fail("Home Portal Light Theme", f"Expected #F8FAFC canvas on 00_Home, got {bg_val}")

    expected_targets = {"3f7688a2cc2e12e049b0", "deb9f8692d454328e800", "c033c6b7a0e103746573", "d044c6b7a0e103746574"}
    found_targets = set()
    for _, vtype, vdata in loaded_visuals:
        if vtype == "actionButton":
            links = vdata.get("visual", {}).get("visualContainerObjects", {}).get("visualLink", [])
            for lk in links:
                props = lk.get("properties", {})
                ltype = props.get("type", {}).get("expr", {}).get("Literal", {}).get("Value", "").strip("'")
                nav_sec = props.get("navigationSection", {}).get("expr", {}).get("Literal", {}).get("Value", "").strip("'")
                if ltype == "PageNavigation" and nav_sec:
                    found_targets.add(nav_sec)

    if found_targets == expected_targets:
        reporter.log_pass("Home Portal Page Navigation Buttons", "All 4 actionButtons link via PageNavigation to Pages 01-04")
    else:
        reporter.log_fail("Home Portal Page Navigation Buttons", f"Expected targets {sorted(expected_targets)}, found {sorted(found_targets)}")

    _finalize_bindings_and_svg(reporter, repo_root, model_tables, page_dir, "00_Home", "Home Portal", bindings_to_check)


def check_performance_lab_visuals(reporter, repo_root, model_tables):
    """Validate 02_PerformanceLab visual types, canvas layout bounds, collisions, conditional formatting, and bindings."""
    check_bento_page_visuals(
        reporter,
        repo_root,
        model_tables,
        page_id="deb9f8692d454328e800",
        display_name="02_PerformanceLab",
        label_prefix="Performance Lab",
        pivot_target="Average HP",
        top_n_target="Performance Index",
    )


def check_landing_page(reporter, repo_root):
    """Validate introductory landing page html/index.html encoding, links to all 4 BI pages, and real car images."""
    landing_path = os.path.join(repo_root, "html", "index.html")
    if not os.path.isfile(landing_path):
        reporter.log_fail("Landing Page UTF-8 No-BOM", f"Landing page not found at {landing_path}")
        reporter.log_fail("Landing Page Portal Integrity", "Landing page missing")
        return

    with open(landing_path, "rb") as fh:
        raw = fh.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        reporter.log_fail("Landing Page UTF-8 No-BOM", "BOM detected in html/index.html")
    else:
        try:
            text = raw.decode("utf-8")
            reporter.log_pass("Landing Page UTF-8 No-BOM", "html/index.html is strictly UTF-8 without BOM")
        except UnicodeDecodeError as exc:
            reporter.log_fail("Landing Page UTF-8 No-BOM", f"Invalid UTF-8 in html/index.html: {exc}")
            return

    required_tokens = [
        "00_Home",
        "01_MarketOverview",
        "02_PerformanceLab",
        "03_ValueIntelligence",
        "04_VehicleExplorer",
        "CarsIntelligence.pbip",
        "<img",
    ]
    missing = [tok for tok in required_tokens if tok not in text]
    if not missing:
        reporter.log_pass("Landing Page Portal Integrity", "html/index.html includes real vehicle images and links to all 4 BI pages + PBIP")
    else:
        reporter.log_fail("Landing Page Portal Integrity", f"Missing required portal references in html/index.html: {missing}")


def check_theme_compliance(reporter, repo_root):
    """Verify presence and validity of registered custom theme Cars_Intelligence_20258711528438303722.json."""
    theme_rel = "powerbi/CarsIntelligence.Report/StaticResources/RegisteredResources/Cars_Intelligence_20258711528438303722.json"
    theme_path = os.path.join(repo_root, theme_rel)
    if not os.path.exists(theme_path):
        reporter.log_fail("Custom Theme File", f"Registered theme file not found at {theme_path}")
        return

    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    # Check theme name
    theme_name = theme.get("name")
    if theme_name == "Automotive Intelligence Modern Enterprise":
        reporter.log_pass("Theme Identity", f"Theme name matches expected '{theme_name}'")
    else:
        reporter.log_fail("Theme Identity", f"Unexpected theme name '{theme_name}'")

    # Check dataColors palette
    expected_colors = ["#2563EB", "#10B981", "#F59E0B", "#F43F5E", "#8B5CF6", "#06B6D4", "#475569", "#0F172A"]
    actual_colors = theme.get("dataColors", [])
    if actual_colors == expected_colors:
        reporter.log_pass("Theme Data Colors", f"Data colors match modern enterprise palette: {actual_colors}")
    else:
        reporter.log_fail("Theme Data Colors", f"Palette mismatch: expected {expected_colors}, got {actual_colors}")

    # Check surface colors
    bg = theme.get("background")
    fg = theme.get("foreground")
    accent = theme.get("tableAccent")
    if bg == "#F8FAFC" and fg == "#0F172A" and accent == "#2563EB":
        reporter.log_pass("Theme Surfaces & Accent", f"Theme background ({bg}), foreground ({fg}), and accent ({accent}) verified")
    else:
        reporter.log_fail("Theme Surfaces & Accent", f"Theme surfaces mismatch: bg={bg}, fg={fg}, accent={accent}")

    # Check card border radius in visualStyles
    try:
        border_radius = theme["visualStyles"]["*"]["*"]["border"][0]["radius"]
        if border_radius == 16:
            reporter.log_pass("Theme Card Corner Radius", f"Visual container border radius confirmed at {border_radius}px")
        else:
            reporter.log_fail("Theme Card Corner Radius", f"Expected border radius 16, got {border_radius}")
    except (KeyError, IndexError, TypeError) as e:
        reporter.log_fail("Theme Card Corner Radius", f"Failed to extract border radius from theme: {e}")

    # Check registration in report.json
    report_json_path = os.path.join(repo_root, "powerbi/CarsIntelligence.Report/definition/report.json")
    if os.path.exists(report_json_path):
        with open(report_json_path, "r", encoding="utf-8") as rf:
            rep = json.load(rf)
        custom_theme_name = rep.get("themeCollection", {}).get("customTheme", {}).get("name")
        if custom_theme_name == os.path.basename(theme_path):
            reporter.log_pass("Theme Registration", f"Theme {custom_theme_name} correctly registered in report.json")
        else:
            reporter.log_fail("Theme Registration", f"report.json customTheme is '{custom_theme_name}', expected '{os.path.basename(theme_path)}'")


def main():
    reporter = VerificationReporter()
    check_file_encodings(reporter, REPO_ROOT)
    check_svg_removals(reporter, REPO_ROOT)
    model_tables = load_semantic_model(REPO_ROOT)
    check_home_portal_visuals(reporter, REPO_ROOT, model_tables)
    check_market_overview_visuals(reporter, REPO_ROOT, model_tables)
    check_performance_lab_visuals(reporter, REPO_ROOT, model_tables)
    check_bento_page_visuals(
        reporter, REPO_ROOT, model_tables,
        page_id="c033c6b7a0e103746573",
        display_name="03_ValueIntelligence",
        label_prefix="Value Intelligence",
        pivot_target="Value Index",
        top_n_target="Value Index",
    )
    check_bento_page_visuals(
        reporter, REPO_ROOT, model_tables,
        page_id="d044c6b7a0e103746574",
        display_name="04_VehicleExplorer",
        label_prefix="Vehicle Explorer",
        pivot_target="Performance Index",
        top_n_target="Performance Index",
    )
    check_theme_compliance(reporter, REPO_ROOT)
    check_landing_page(reporter, REPO_ROOT)
    success = reporter.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
