"""
AZOTH Capability Test Runner — P2-T1.
Discovers and runs all test_*.py files in CORE/tests/.
Returns structured results; writes report to WORKSPACE/test_results.md.
"""

import importlib.util, sys, os, time, traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

HARNESS_DIR = Path(__file__).parent.parent
TESTS_DIR = Path(__file__).parent / "tests"
WORKSPACE = HARNESS_DIR / "WORKSPACE"

@dataclass
class TestResult:
    module: str
    name: str
    passed: bool
    skipped: bool
    message: str
    duration: float

@dataclass
class TestReport:
    results: list = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed and not r.skipped)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed and not r.skipped)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def all_pass(self) -> bool:
        return self.failed == 0

    def summary(self) -> str:
        lines = [
            f"AZOTH Capability Tests — {time.strftime('%Y-%m-%d %H:%M')}",
            f"PASS: {self.passed}  FAIL: {self.failed}  SKIP: {self.skipped}  TOTAL: {self.total}",
            "",
        ]
        current_module = None
        for r in self.results:
            if r.module != current_module:
                current_module = r.module
                lines.append(f"## {r.module}")
            if r.skipped:
                sym = "⏭"
            elif r.passed:
                sym = "✓"
            else:
                sym = "✗"
            lines.append(f"  {sym} {r.name}  [{r.duration*1000:.0f}ms]  {r.message}")
        lines.append("")
        if self.all_pass:
            lines.append("ALL TESTS PASS — forge gate clear")
        else:
            lines.append(f"FAIL — {self.failed} test(s) failed. Forge blocked until resolved.")
        return "\n".join(lines)


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover_test_files(tests_dir: Path = TESTS_DIR) -> list:
    return sorted(tests_dir.glob("test_*.py"))


def run_file(path: Path) -> list:
    results = []
    module_name = path.stem
    try:
        mod = _load_module(path)
    except Exception as e:
        results.append(TestResult(
            module=module_name, name="[import]",
            passed=False, skipped=False,
            message=f"IMPORT ERROR: {e}",
            duration=0.0,
        ))
        return results

    for name in dir(mod):
        if not name.startswith("test_"):
            continue
        fn = getattr(mod, name)
        if not callable(fn):
            continue
        t0 = time.perf_counter()
        try:
            ret = fn()
            duration = time.perf_counter() - t0
            if ret is None:
                results.append(TestResult(module=module_name, name=name,
                    passed=False, skipped=True, message="(no return)", duration=duration))
            elif isinstance(ret, tuple):
                status, msg = ret
                if status is None:
                    results.append(TestResult(module=module_name, name=name,
                        passed=False, skipped=True, message=msg, duration=duration))
                else:
                    results.append(TestResult(module=module_name, name=name,
                        passed=bool(status), skipped=False, message=msg, duration=duration))
            else:
                results.append(TestResult(module=module_name, name=name,
                    passed=bool(ret), skipped=False, message="(bool return)", duration=duration))
        except AssertionError as e:
            duration = time.perf_counter() - t0
            results.append(TestResult(module=module_name, name=name,
                passed=False, skipped=False, message=f"ASSERT: {e}", duration=duration))
        except Exception as e:
            duration = time.perf_counter() - t0
            tb = traceback.format_exc().strip().split("\n")[-1]
            results.append(TestResult(module=module_name, name=name,
                passed=False, skipped=False, message=f"ERROR: {tb}", duration=duration))
    return results


def run_all(tests_dir: Path = TESTS_DIR, verbose: bool = True) -> TestReport:
    report = TestReport()
    files = discover_test_files(tests_dir)
    if not files:
        print("  ⚠ No test files found in", tests_dir)
        return report
    for f in files:
        results = run_file(f)
        report.results.extend(results)
        if verbose:
            for r in results:
                sym = "⏭" if r.skipped else ("✓" if r.passed else "✗")
                tag = "\033[93m" if r.skipped else ("\033[92m" if r.passed else "\033[91m")
                print(f"  {tag}{sym}\033[0m {r.module}::{r.name}  {r.message}")
    return report


def run_and_write(tests_dir: Path = TESTS_DIR, verbose: bool = True) -> TestReport:
    report = run_all(tests_dir=tests_dir, verbose=verbose)
    WORKSPACE.mkdir(exist_ok=True)
    out = WORKSPACE / "test_results.md"
    out.write_text(report.summary())
    print(f"\n  Report → {out}")
    return report


if __name__ == "__main__":
    report = run_and_write()
    sys.exit(0 if report.all_pass else 1)
