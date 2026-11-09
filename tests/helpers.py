"""
Cars Intelligence 2025 - Test Infrastructure Helpers
Provides robust parsers, loaders, and invariant validators for PBIP TMDL and JSON artifacts.
"""

import os
import glob
import json
import re
from typing import Dict, List, Any, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEMANTIC_MODEL_DIR = os.path.join(REPO_ROOT, "powerbi", "CarsIntelligence.SemanticModel", "definition")
REPORT_DEF_DIR = os.path.join(REPO_ROOT, "powerbi", "CarsIntelligence.Report", "definition")
PAGE1_DIR = os.path.join(REPORT_DEF_DIR, "pages", "3f7688a2cc2e12e049b0")
PAGE2_DIR = os.path.join(REPORT_DEF_DIR, "pages", "deb9f8692d454328e800")
PAGE_DIR = PAGE1_DIR
THEME_PATH = os.path.join(
    REPO_ROOT,
    "powerbi",
    "CarsIntelligence.Report",
    "StaticResources",
    "RegisteredResources",
    "Cars_Intelligence_20258711528438303722.json"
)
VERIFY_SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "verify_report.py")

class TMDLTable:
    def __init__(self, name: str, file_path: str):
        self.name = name
        self.file_path = file_path
        self.lineage_tag: Optional[str] = None
        self.measures: Dict[str, Dict[str, Any]] = {}
        self.columns: Dict[str, Dict[str, Any]] = {}
        self.raw_text: str = ""
        self.raw_bytes: bytes = b""

class TMDLModel:
    def __init__(self):
        self.tables: Dict[str, TMDLTable] = {}
        self.relationships: List[Dict[str, str]] = []
        self.files: Dict[str, str] = {}

def load_semantic_model() -> TMDLModel:
    """Parses all TMDL files in the semantic model definition."""
    model = TMDLModel()
    tmdl_pattern = os.path.join(SEMANTIC_MODEL_DIR, "**", "*.tmdl")
    for file_path in glob.glob(tmdl_pattern, recursive=True):
        rel_path = os.path.relpath(file_path, REPO_ROOT)
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        raw_text = raw_bytes.decode("utf-8")
        model.files[rel_path] = raw_text

        # Table files
        if os.path.dirname(file_path).endswith("tables"):
            table_name = os.path.splitext(os.path.basename(file_path))[0]
            # Match table header if quoted or unquoted
            t_match = re.search(r"^table\s+(?:(?:\'([^\']+)\')|([^\s\r\n=]+))", raw_text, re.MULTILINE)
            if t_match:
                table_name = t_match.group(1) or t_match.group(2)
            
            table = TMDLTable(table_name, file_path)
            table.raw_bytes = raw_bytes
            table.raw_text = raw_text

            # Table lineageTag
            lt_match = re.search(r"^\tlineageTag:\s*([a-f0-9\-]+)", raw_text, re.MULTILINE)
            if lt_match:
                table.lineage_tag = lt_match.group(1)

            # Parse measures
            # measure syntax: measure 'Name' = ... or measure Name = ...
            measure_blocks = re.split(r"^\tmeasure\s+", raw_text, flags=re.MULTILINE)
            for block in measure_blocks[1:]:
                header_match = re.match(r"^(?:(?:\'([^\']+)\')|([^\s\r\n=]+))\s*=\s*(.*)", block)
                if header_match:
                    m_name = header_match.group(1) or header_match.group(2)
                    m_dax_start = header_match.group(3)
                    lt = re.search(r"^\t\tlineageTag:\s*([a-f0-9\-]+)", block, re.MULTILINE)
                    fs = re.search(r"^\t\tformatString:\s*(.+)", block, re.MULTILINE)
                    df = re.search(r"^\t\tdisplayFolder:\s*(.+)", block, re.MULTILINE)
                    table.measures[m_name] = {
                        "name": m_name,
                        "lineageTag": lt.group(1) if lt else None,
                        "formatString": fs.group(1).strip() if fs else None,
                        "displayFolder": df.group(1).strip() if df else None,
                        "block": block
                    }

            # Parse columns
            # column syntax: column 'Name' or column Name
            col_blocks = re.split(r"^\tcolumn\s+", raw_text, flags=re.MULTILINE)
            for block in col_blocks[1:]:
                header_match = re.match(r"^(?:(?:\'([^\']+)\')|([^\s\r\n=]+))(?:\s*=\s*(.*))?", block)
                if header_match:
                    c_name = header_match.group(1) or header_match.group(2)
                    has_equals = bool(header_match.group(3) is not None or " = " in block.splitlines()[0] or block.splitlines()[0].endswith("="))
                    has_source_col = bool(re.search(r"^\t\tsourceColumn:", block, re.MULTILINE))
                    dt = re.search(r"^\t\tdataType:\s*([^\s\r\n]+)", block, re.MULTILINE)
                    lt = re.search(r"^\t\tlineageTag:\s*([a-f0-9\-]+)", block, re.MULTILINE)
                    is_calc = has_equals or (not has_source_col)
                    table.columns[c_name] = {
                        "name": c_name,
                        "dataType": dt.group(1) if dt else None,
                        "lineageTag": lt.group(1) if lt else None,
                        "isCalculated": is_calc,
                        "block": block
                    }

            model.tables[table_name] = table

        # Relationships file
        elif os.path.basename(file_path) == "relationships.tmdl":
            rel_blocks = re.split(r"^relationship\s+", raw_text, flags=re.MULTILINE)
            for rb in rel_blocks[1:]:
                from_m = re.search(r"^\tfromColumn:\s*(.+)", rb, re.MULTILINE)
                to_m = re.search(r"^\ttoColumn:\s*(.+)", rb, re.MULTILINE)
                if from_m and to_m:
                    model.relationships.append({
                        "fromColumn": from_m.group(1).strip(),
                        "toColumn": to_m.group(1).strip()
                    })

    return model

class VisualContainer:
    def __init__(self, visual_id: str, file_path: str, data: Dict[str, Any]):
        self.id = visual_id
        self.file_path = file_path
        self.data = data
        self.pos = data.get("position", {})
        self.x = self.pos.get("x", 0)
        self.y = self.pos.get("y", 0)
        self.width = self.pos.get("width", 0)
        self.height = self.pos.get("height", 0)
        self.z = self.pos.get("z", 0)
        self.visual_type = data.get("visual", {}).get("visualType", "unknown")

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

class ReportPage:
    def __init__(self, page_data: Dict[str, Any], visuals: List[VisualContainer]):
        self.data = page_data
        self.name = page_data.get("name", "")
        self.display_name = page_data.get("displayName", "")
        self.width = page_data.get("width", 0)
        self.height = page_data.get("height", 0)
        self.visuals = visuals

def load_report_page(page_dir: str = PAGE1_DIR) -> ReportPage:
    """Loads a Power BI report page and all its visual containers."""
    page_json_path = os.path.join(page_dir, "page.json")
    with open(page_json_path, "r", encoding="utf-8") as f:
        page_data = json.load(f)

    visuals: List[VisualContainer] = []
    visual_pattern = os.path.join(page_dir, "visuals", "*", "visual.json")
    for vf in glob.glob(visual_pattern):
        vid = os.path.basename(os.path.dirname(vf))
        with open(vf, "r", encoding="utf-8") as f:
            v_data = json.load(f)
        visuals.append(VisualContainer(vid, vf, v_data))

    return ReportPage(page_data, visuals)

def load_market_overview_page() -> ReportPage:
    """Loads page 01_MarketOverview and all visual containers."""
    return load_report_page(PAGE1_DIR)

def load_performance_lab_page() -> ReportPage:
    """Loads page 02_PerformanceLab and all visual containers."""
    return load_report_page(PAGE2_DIR)

def load_theme() -> Dict[str, Any]:
    """Loads the registered modern enterprise theme."""
    with open(THEME_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_visual_bindings(visual_json: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """
    Recursively extracts all (binding_type, entity, property) from a visual container JSON.
    binding_type is 'Measure' or 'Column'.
    """
    bindings: List[Tuple[str, str, str]] = []

    def _traverse(node: Any):
        if isinstance(node, dict):
            if "Measure" in node and isinstance(node["Measure"], dict):
                m = node["Measure"]
                prop = m.get("Property")
                ent = m.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if prop and ent:
                    bindings.append(("Measure", ent, prop))
            elif "Column" in node and isinstance(node["Column"], dict):
                c = node["Column"]
                prop = c.get("Property")
                ent = c.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if prop and ent:
                    bindings.append(("Column", ent, prop))
            for val in node.values():
                _traverse(val)
        elif isinstance(node, list):
            for item in node:
                _traverse(item)

    _traverse(visual_json)
    return bindings

def check_bounding_box_overlap(v1: VisualContainer, v2: VisualContainer) -> bool:
    """Returns True if two visual containers strictly overlap (area intersection > 0)."""
    # Overlap occurs if one is NOT completely to the left, right, above, or below the other
    if v1.right <= v2.x or v2.right <= v1.x:
        return False
    if v1.bottom <= v2.y or v2.bottom <= v1.y:
        return False
    return True
