#!/usr/bin/env python3
"""
Cars Intelligence 2025 - Authoritative 4-Tier E2E Test Suite Runner
Executes comprehensive opaque-box E2E test suites across Tiers 1-4,
reports granular pass/fail counts per tier and feature, and exits with code 0 on success.
"""

import sys
import os
import unittest
import time
import argparse
from typing import Dict, List, Any

# Ensure project root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.test_tier1_features import TestTier1Features
from tests.test_tier2_boundaries import TestTier2Boundaries
from tests.test_tier3_combinations import TestTier3Combinations
from tests.test_tier4_scenarios import TestTier4Scenarios

FEATURE_MAP = {
    1: "Purge Legacy SVG Measures",
    2: "Purge Legacy SVG Column",
    3: "Semantic Model Integrity",
    4: "Deploy Automated Verification Script",
    5: "Pure Typography KPI Cards",
    6: "Performance Index Cockpit",
    7: "Average HP by Segment Tier",
    8: "Market Positioning Matrix",
    9: "Powertrain & Segment Heatmap",
    10: "Top Value Leaders Table",
    11: "Dropdown Slicers",
    12: "Header & Navigation",
    13: "Automotive Studio Bento Grid",
    14: "Theme Styling",
    15: "Strict UTF-8 Without BOM",
    16: "Performance Lab Bento Grid Geometry",
    17: "Performance Lab KPI Cards",
    18: "Performance Lab Telemetry Cockpit Gauge",
    19: "Performance Lab Sprint Benchmark Bar Chart",
    20: "Performance Lab Dynamics Scatter Matrix",
    21: "Performance Lab Powertrain Matrix",
    22: "Performance Lab Track Leaderboard Table",
    23: "Performance Lab Slicers & Page Navigation",
    24: "Performance Lab Theme Styling",
    25: "Performance Lab DAX Measure Bindings"
}

class DetailedTestResult(unittest.TestResult):
    def __init__(self, verbosity=1):
        super().__init__()
        self.verbosity = verbosity
        self.test_records = []

    def startTest(self, test):
        super().startTest(test)
        if self.verbosity > 1:
            sys.stdout.write(f"  RUN: {test.id()} ... ")
            sys.stdout.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_records.append((test, "PASS", ""))
        if self.verbosity > 1:
            print("OK")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        msg = self._exc_info_to_string(err, test)
        self.test_records.append((test, "FAIL", msg))
        if self.verbosity > 1:
            print("FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        msg = self._exc_info_to_string(err, test)
        self.test_records.append((test, "ERROR", msg))
        if self.verbosity > 1:
            print("ERROR")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.test_records.append((test, "SKIP", reason))
        if self.verbosity > 1:
            print(f"SKIP ({reason})")

def run_suite(verbosity=1, tier_filter=None, feature_filter=None) -> int:
    start_time = time.time()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tier_classes = {
        1: ("Tier 1: Feature Coverage (Happy Path)", TestTier1Features),
        2: ("Tier 2: Boundary & Corner Cases", TestTier2Boundaries),
        3: ("Tier 3: Cross-Feature Combinations (Pairwise)", TestTier3Combinations),
        4: ("Tier 4: Real-World Application Scenarios", TestTier4Scenarios),
    }

    selected_tiers = [tier_filter] if tier_filter else [1, 2, 3, 4]

    tier_results = {}

    total_passed = 0
    total_failed = 0
    total_errors = 0

    print("=" * 80)
    print("CARS INTELLIGENCE 2025 - AUTHORITATIVE E2E 4-TIER TEST SUITE")
    print("=" * 80)
    print(f"Target Working Directory: {REPO_ROOT}")
    print(f"Selected Tiers: {selected_tiers}")
    if feature_filter:
        print(f"Feature Filter: F{feature_filter} - {FEATURE_MAP.get(feature_filter)}")
    print("-" * 80)

    for tier_num in selected_tiers:
        tier_title, test_class = tier_classes[tier_num]
        sub_suite = unittest.TestSuite()

        # If feature filter is applied, only select matching tests for Tier 1 and 2
        for test_name in loader.getTestCaseNames(test_class):
            if feature_filter:
                f_prefix = f"test_f{feature_filter}_"
                if not test_name.startswith(f_prefix):
                    continue
            sub_suite.addTest(test_class(test_name))

        runner = unittest.TextTestRunner(verbosity=0)
        result = DetailedTestResult(verbosity=verbosity)
        sub_suite.run(result)

        t_pass = len([r for r in result.test_records if r[1] == "PASS"])
        t_fail = len([r for r in result.test_records if r[1] == "FAIL"])
        t_err = len([r for r in result.test_records if r[1] == "ERROR"])

        total_passed += t_pass
        total_failed += t_fail
        total_errors += t_err

        tier_results[tier_num] = {
            "title": tier_title,
            "total": len(result.test_records),
            "passed": t_pass,
            "failed": t_fail,
            "errors": t_err,
            "records": result.test_records
        }

    elapsed = time.time() - start_time

    # Print Detailed Per-Tier Breakdown
    for tier_num in selected_tiers:
        tr = tier_results[tier_num]
        status = "PASSED" if (tr["failed"] == 0 and tr["errors"] == 0 and tr["total"] > 0) else ("EMPTY" if tr["total"] == 0 else "FAILED")
        print(f"\n[{status}] {tr['title']}")
        print(f"      Total: {tr['total']} | Passed: {tr['passed']} | Failed: {tr['failed']} | Errors: {tr['errors']}")

        # Feature Breakdown for Tiers 1 and 2
        if tier_num in (1, 2) and tr["total"] > 0:
            for f_idx in sorted(FEATURE_MAP.keys()):
                f_name = FEATURE_MAP[f_idx]
                f_prefix = f"test_f{f_idx}_"
                f_records = [r for r in tr["records"] if r[0]._testMethodName.startswith(f_prefix)]
                f_pass = len([r for r in f_records if r[1] == "PASS"])
                if f_records:
                    status_flag = "[OK]" if f_pass == len(f_records) else "[FAIL]"
                    print(f"        {status_flag} F{f_idx:02d}: {f_name:<44} ({f_pass}/{len(f_records)} passed)")

        # Print failures if any
        if tr["failed"] > 0 or tr["errors"] > 0:
            for test, outcome, msg in tr["records"]:
                if outcome in ("FAIL", "ERROR"):
                    print(f"\n      --> {outcome}: {test.id()}")
                    for line in msg.strip().splitlines()[-6:]:
                        print(f"          {line}")

    print("\n" + "=" * 80)
    print("E2E SUITE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests Executed : {total_passed + total_failed + total_errors}")
    print(f"Total Passed         : {total_passed}")
    print(f"Total Failed         : {total_failed}")
    print(f"Total Errors         : {total_errors}")
    print(f"Execution Time       : {elapsed:.2f} seconds")
    print(f"Overall Status       : {'100% PASS' if (total_failed == 0 and total_errors == 0 and total_passed > 0) else 'FAIL'}")
    print("=" * 80 + "\n")

    return 0 if (total_failed == 0 and total_errors == 0 and total_passed > 0) else 1

def main():
    parser = argparse.ArgumentParser(description="Cars Intelligence 2025 E2E Test Suite Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Detailed verbose output")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4], help="Run only specified tier")
    parser.add_argument("--feature", type=int, choices=list(FEATURE_MAP.keys()), help="Filter by feature number (1-25)")
    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1
    exit_code = run_suite(verbosity=verbosity, tier_filter=args.tier, feature_filter=args.feature)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
