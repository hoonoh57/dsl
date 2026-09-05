from __future__ import annotations

import argparse
import io
import pathlib
import sys
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MAX_TRACE_LINES = 18


def _tail_traceback(text: str) -> list[str]:
    lines = [line.rstrip() for line in str(text).splitlines()]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines[-MAX_TRACE_LINES:]


def _test_id(test: unittest.case.TestCase) -> str:
    try:
        return test.id()
    except Exception:
        return str(test)


def run(names: list[str]) -> int:
    if not names:
        print("[ERROR] Focused tests require at least one test module or test id.", file=sys.stderr)
        return 2

    suite = unittest.defaultTestLoader.loadTestsFromNames(names)
    sink = io.StringIO()
    result = unittest.TextTestRunner(
        stream=sink,
        verbosity=0,
        buffer=True,
    ).run(suite)

    if result.wasSuccessful():
        print(f"[PASS] Focused tests passed ({result.testsRun}).")
        return 0

    failures = list(result.failures) + list(result.errors)
    print(f"[ERROR] Focused tests failed ({len(failures)} of {result.testsRun}).", file=sys.stderr)
    for test, traceback_text in failures:
        print(f"[FAIL] {_test_id(test)}", file=sys.stderr)
        for line in _tail_traceback(traceback_text):
            print(f"  {line}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run unittest targets with compact operator output.")
    parser.add_argument("tests", nargs="+", help="unittest module, class, or test id")
    args = parser.parse_args()
    return run(args.tests)


if __name__ == "__main__":
    raise SystemExit(main())
