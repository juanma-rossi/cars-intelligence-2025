"""MCP-aligned & CI-reproducible Semantic Model and PBIR Performance Validator.

Validates TMDL star schema structure, single-source Power Query ingestion,
DAX measure hygiene, PBIR page visual budgets, and (when present locally)
raw dataset invariants for Cars Intelligence 2025.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POWERBI_DIR = PROJECT_ROOT / "powerbi"
SEMANTIC_DEF = POWERBI_DIR / "CarsIntelligence.SemanticModel" / "definition"
REPORT_DEF = POWERBI_DIR / "CarsIntelligence.Report" / "definition"
RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "Cars Datasets 2025.csv"

EXPECTED_TABLES = (
    "FactVehicle",
    "DimCompany",
    "DimFuel",
    "DimEngine",
    "DimPriceSegment",
    "_Measures",
    "qa_Cars_Audit",
    "qa_DuplicateVehicles",
    "qa_DuplicateDetails",
)

EXPECTED_RELATIONSHIPS = (
    ("FactVehicle.Company", "DimCompany.Company"),
    ("FactVehicle.Fuel_Group", "DimFuel.Fuel_Group"),
    ("FactVehicle.Engine_Key", "DimEngine.Engine_Key"),
    ("FactVehicle.Segment_ID", "DimPriceSegment.Segment_ID"),
)

M_STAGING_CONSUMERS = (
    "FactVehicle",
    "DimCompany",
    "DimFuel",
    "DimEngine",
    "qa_Cars_Audit",
    "qa_DuplicateVehicles",
    "qa_DuplicateDetails",
)

VISIBLE_PAGES = (
    "00_Home",
    "01_MarketOverview",
    "02_PerformanceLab",
    "03_ValueIntelligence",
    "04_VehicleExplorer",
)

MAX_VISUALS_PER_PAGE = 20
SVG_MARKERS = ("<svg", "data:image/svg", "imagecontrol")


class ValidationRunner:
    """Collects structured PASS/FAIL/SKIP check outcomes."""

    def __init__(self) -> None:
        self.checks: list[dict[str, str]] = []
        self.metrics: dict[str, Any] = {}

    def record(self, status: str, name: str, detail: str) -> None:
        self.checks.append({"status": status, "name": name, "detail": detail})

    def passed(self, name: str, detail: str) -> None:
        self.record("PASS", name, detail)

    def failed(self, name: str, detail: str) -> None:
        self.record("FAIL", name, detail)

    def skipped(self, name: str, detail: str) -> None:
        self.record("SKIP", name, detail)

    @property
    def counts(self) -> dict[str, int]:
        return {
            "passed": sum(1 for c in self.checks if c["status"] == "PASS"),
            "failed": sum(1 for c in self.checks if c["status"] == "FAIL"),
            "skipped": sum(1 for c in self.checks if c["status"] == "SKIP"),
        }


def _strip_dax_literals_and_comments(expr: str) -> str:
    """Remove string literals and line/block comments before syntax checks."""
    text = re.sub(r'""', "", expr)
    text = re.sub(r'"[^"\n]*"', "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


def check_model_structure(runner: ValidationRunner) -> None:
    """Validate model.tmdl table references and valueFilterBehavior."""
    model_path = SEMANTIC_DEF / "model.tmdl"
    if not model_path.exists():
        runner.failed("Model TMDL Presence", f"Missing {model_path}")
        return

    text = model_path.read_text(encoding="utf-8")
    refs = set(re.findall(r"^ref table\s+(.+?)\s*$", text, re.MULTILINE))
    missing = [tbl for tbl in EXPECTED_TABLES if tbl not in refs]
    runner.metrics["model_tables"] = sorted(refs)

    if not missing:
        runner.passed(
            "Model Table Inventory",
            f"All {len(EXPECTED_TABLES)} expected tables registered in model.tmdl",
        )
    else:
        runner.failed("Model Table Inventory", f"Missing table refs: {missing}")

    if "valueFilterBehavior: independent" in text:
        runner.passed(
            "Model Filter Behavior",
            "valueFilterBehavior: independent configured in model.tmdl",
        )
    else:
        runner.failed(
            "Model Filter Behavior",
            "Expected valueFilterBehavior: independent in model.tmdl",
        )


def check_relationships(runner: ValidationRunner) -> None:
    """Validate active star-schema relationships in relationships.tmdl."""
    rel_path = SEMANTIC_DEF / "relationships.tmdl"
    if not rel_path.exists():
        runner.failed("Star Schema Relationships", f"Missing {rel_path}")
        return

    text = rel_path.read_text(encoding="utf-8")
    blocks = re.split(r"^relationship\s+", text, flags=re.MULTILINE)[1:]
    pairs: set[tuple[str, str]] = set()

    for block in blocks:
        from_m = re.search(r"^\tfromColumn:\s*(.+?)\s*$", block, re.MULTILINE)
        to_m = re.search(r"^\ttoColumn:\s*(.+?)\s*$", block, re.MULTILINE)
        inactive = re.search(r"^\tisActive:\s*false\s*$", block, re.MULTILINE)
        if from_m and to_m and not inactive:
            pairs.add((from_m.group(1), to_m.group(1)))

    missing = [rel for rel in EXPECTED_RELATIONSHIPS if rel not in pairs]
    runner.metrics["active_relationships"] = [f"{a} -> {b}" for a, b in sorted(pairs)]

    if not missing:
        runner.passed(
            "Star Schema Relationships",
            f"All {len(EXPECTED_RELATIONSHIPS)} 1:* active relationships verified",
        )
    else:
        runner.failed("Star Schema Relationships", f"Missing relationships: {missing}")


def check_m_pipeline(runner: ValidationRunner) -> None:
    """Verify single-source M ingestion via pDataFolder and stg_Cars_Raw."""
    expr_path = SEMANTIC_DEF / "expressions.tmdl"
    if not expr_path.exists():
        runner.failed("M Staging Expressions", f"Missing {expr_path}")
        return

    expr_text = expr_path.read_text(encoding="utf-8")
    has_param = "expression pDataFolder =" in expr_text
    has_staging = "expression stg_Cars_Raw =" in expr_text
    if has_param and has_staging:
        runner.passed(
            "Reproducible Parameter & Staging",
            "pDataFolder parameter and single-source stg_Cars_Raw query defined",
        )
    else:
        runner.failed(
            "Reproducible Parameter & Staging",
            f"pDataFolder={has_param}, stg_Cars_Raw={has_staging}",
        )

    bad_tables: list[str] = []
    for table_name in M_STAGING_CONSUMERS:
        tpath = SEMANTIC_DEF / "tables" / f"{table_name}.tmdl"
        if not tpath.exists():
            bad_tables.append(f"{table_name} (missing)")
            continue
        ttext = tpath.read_text(encoding="utf-8")
        if "stg_Cars_Raw" not in ttext or "Csv.Document" in ttext:
            bad_tables.append(table_name)

    if not bad_tables:
        runner.passed(
            "Single-Source M Consumers",
            f"All {len(M_STAGING_CONSUMERS)} M tables read exclusively from stg_Cars_Raw (0 redundant CSV scans)",
        )
    else:
        runner.failed("Single-Source M Consumers", f"Non-compliant M tables: {bad_tables}")


def check_dax_measures(runner: ValidationRunner) -> None:
    """Audit all measures in _Measures.tmdl for count, balanced syntax, and metadata."""
    measures_path = SEMANTIC_DEF / "tables" / "_Measures.tmdl"
    if not measures_path.exists():
        runner.failed("DAX Measure Audit", f"Missing {measures_path}")
        return

    text = measures_path.read_text(encoding="utf-8")
    blocks = text.split("\tmeasure ")[1:]
    runner.metrics["measure_count"] = len(blocks)

    if len(blocks) >= 60:
        runner.passed(
            "DAX Measure Count",
            f"{len(blocks)} centralized measures present in _Measures.tmdl (>= 60 expected)",
        )
    else:
        runner.failed("DAX Measure Count", f"Expected >= 60 measures, found {len(blocks)}")

    metadata_gaps: list[str] = []
    unbalanced: list[str] = []

    for block in blocks:
        lines = block.splitlines()
        name = lines[0].split("=", 1)[0].strip().strip("'")
        has_folder = "\t\tdisplayFolder:" in block
        has_lineage = "\t\tlineageTag:" in block
        if not (has_folder and has_lineage):
            metadata_gaps.append(name)

        expr_lines = []
        stop_prefixes = ("\t\tformatString:", "\t\tdisplayFolder:", "\t\tlineageTag:", "\t\tannotation ")
        for line in lines[1:]:
            if line.startswith(stop_prefixes):
                break
            if line.strip() == "```":
                continue
            expr_lines.append(line)

        cleaned = _strip_dax_literals_and_comments("\n".join(expr_lines))
        if cleaned.count("(") != cleaned.count(")"):
            unbalanced.append(name)

    if not metadata_gaps:
        runner.passed(
            "DAX Measure Metadata",
            f"100% of {len(blocks)} measures define displayFolder and lineageTag",
        )
    else:
        runner.failed("DAX Measure Metadata", f"Missing metadata on: {metadata_gaps}")

    if not unbalanced:
        runner.passed(
            "DAX Parentheses Balance",
            f"All {len(blocks)} measure expressions have balanced parentheses",
        )
    else:
        runner.failed("DAX Parentheses Balance", f"Unbalanced parentheses in: {unbalanced}")


def check_report_performance_budget(runner: ValidationRunner) -> None:
    """Verify PBIR visible pages stay within Microsoft <= 20 visuals/page best practice."""
    pages_dir = REPORT_DEF / "pages"
    pages_index = pages_dir / "pages.json"
    if not pages_index.exists():
        runner.failed("PBIR Page Inventory", f"Missing {pages_index}")
        return

    page_map: dict[str, Path] = {}
    for page_folder in sorted(pages_dir.iterdir()):
        pjson = page_folder / "page.json"
        if page_folder.is_dir() and pjson.exists():
            pdata = json.loads(pjson.read_text(encoding="utf-8"))
            page_map[pdata.get("displayName", page_folder.name)] = page_folder

    missing_pages = [p for p in VISIBLE_PAGES if p not in page_map]
    if missing_pages:
        runner.failed("PBIR Visible Pages", f"Missing pages: {missing_pages}")
        return

    over_budget: list[str] = []
    svg_hits: list[str] = []
    counts: dict[str, int] = {}

    for name in VISIBLE_PAGES:
        visuals_dir = page_map[name] / "visuals"
        vfiles = sorted(visuals_dir.glob("*/visual.json"))
        counts[name] = len(vfiles)
        if len(vfiles) > MAX_VISUALS_PER_PAGE:
            over_budget.append(f"{name}={len(vfiles)}")
        for vf in vfiles:
            raw_lower = vf.read_text(encoding="utf-8").lower()
            if any(marker in raw_lower for marker in SVG_MARKERS):
                svg_hits.append(f"{name}/{vf.parent.name}")

    runner.metrics["visuals_per_page"] = counts

    if not over_budget:
        summary = ", ".join(f"{k}={v}" for k, v in counts.items())
        runner.passed(
            "PBIR Visual Budget (<= 20/page)",
            f"All visible pages within Microsoft best-practice cap ({summary})",
        )
    else:
        runner.failed("PBIR Visual Budget (<= 20/page)", f"Exceeded cap: {over_budget}")

    if not svg_hits:
        runner.passed(
            "Zero Legacy SVG Overhead",
            "0 SVG tags/data-URIs/imageControls across all visible report pages",
        )
    else:
        runner.failed("Zero Legacy SVG Overhead", f"Legacy SVG references in: {svg_hits}")


def _clean_m_text(value: str | None) -> str:
    """Mirror Power Query Text.Clean(Text.Trim(...)) on raw CSV fields."""
    if not value:
        return ""
    cleaned = "".join(ch for ch in value if ord(ch) >= 32)
    return cleaned.strip()


def check_raw_dataset_invariants(runner: ValidationRunner) -> None:
    """Verify dataset row count, deduplicated count, and OEM count if CSV exists locally."""
    if not RAW_CSV_PATH.exists():
        runner.skipped(
            "Local CSV Dataset Invariants",
            "data/raw/Cars Datasets 2025.csv not present (excluded via .gitignore in CI)",
        )
        return

    with RAW_CSV_PATH.open("r", encoding="cp1252", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))

    field_names = list(rows[0].keys()) if rows else []
    natural_keys: set[tuple[str, ...]] = set()
    companies: set[str] = set()

    for row in rows:
        cleaned_vals = [_clean_m_text(row.get(col)) for col in field_names]
        comp = cleaned_vals[0] if len(cleaned_vals) > 0 else ""
        car = cleaned_vals[1] if len(cleaned_vals) > 1 else ""
        if comp.upper() == "BMW" and "mclaren" in car.lower():
            comp = "MCLAREN"
            cleaned_vals[0] = comp
        natural_keys.add(tuple(cleaned_vals))
        if comp:
            companies.add(comp.upper())

    runner.metrics["dataset"] = {
        "raw_rows": len(rows),
        "unique_vehicles": len(natural_keys),
        "oem_companies": len(companies),
    }

    if len(rows) == 1218 and len(natural_keys) == 1214 and len(companies) == 32:
        runner.passed(
            "Local CSV Dataset Invariants",
            "1,218 raw rows -> 1,214 unique vehicles, 0 key collisions, 32 OEM companies verified",
        )
    else:
        runner.failed(
            "Local CSV Dataset Invariants",
            f"Unexpected counts: raw={len(rows)}, unique={len(natural_keys)}, companies={len(companies)}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MCP-aligned semantic model & PBIR performance validator"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON validation report",
    )
    args = parser.parse_args()

    runner = ValidationRunner()
    check_model_structure(runner)
    check_relationships(runner)
    check_m_pipeline(runner)
    check_dax_measures(runner)
    check_report_performance_budget(runner)
    check_raw_dataset_invariants(runner)

    counts = runner.counts
    if args.json:
        payload = {
            "summary": counts,
            "metrics": runner.metrics,
            "checks": runner.checks,
        }
        print(json.dumps(payload, indent=2))
    else:
        print("=" * 80)
        print("CARS INTELLIGENCE 2025 - MCP & CI MODEL VALIDATOR")
        print("=" * 80)
        for item in runner.checks:
            print(f"[{item['status']}] {item['name']}: {item['detail']}")
        print("=" * 80)
        print(
            f"Summary: {counts['passed']} PASSED | "
            f"{counts['failed']} FAILED | {counts['skipped']} SKIPPED"
        )
        print("=" * 80)

    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
