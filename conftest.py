import linecache
import os
import sys
import threading
import trace
from pathlib import Path

import pytest
import django
from django.conf import settings
from django.core.management import call_command


def pytest_addoption(parser):
    parser.addoption(
        "--cov",
        action="append",
        default=[],
        help="Collect trace-based coverage for the given paths",
    )
    parser.addoption(
        "--cov-report",
        action="append",
        default=[],
        help="Choose coverage report formats (term or term-missing)",
    )


def pytest_configure(config=None):
    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_api.settings.test")
        django.setup()

    if config is not None:
        cov_paths = [Path(path).resolve() for path in config.getoption("--cov")]
        config._trace_cov_paths = cov_paths
        config._trace_reports = config.getoption("--cov-report")
        config._trace_tracer = None


def pytest_sessionstart(session):
    if settings.configured:
        call_command("migrate", verbosity=0, run_syncdb=True)

    cov_paths = getattr(session.config, "_trace_cov_paths", [])
    if not cov_paths:
        return

    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix, sys.exec_prefix])
    session.config._trace_tracer = tracer
    tracer_handler = tracer.globaltrace
    sys.settrace(tracer_handler)
    threading.settrace(tracer_handler)


def pytest_sessionfinish(session, exitstatus):
    tracer = getattr(session.config, "_trace_tracer", None)
    if tracer is None:
        return

    sys.settrace(None)
    threading.settrace(None)

    cov_paths = getattr(session.config, "_trace_cov_paths", [])
    reports = getattr(session.config, "_trace_reports", []) or ["term-missing"]
    results = tracer.results()
    coverage_summary = _build_coverage_summary(results, cov_paths)
    _print_coverage(coverage_summary, reports)
    _write_coverage_report(coverage_summary)


@pytest.fixture(autouse=True)
def _flush_db_between_tests():
    if settings.configured:
        call_command("flush", verbosity=0, interactive=False)


def _build_coverage_summary(results, cov_paths):
    summary = []
    for filepath, line_counts in results.counts.items():
        path = Path(filepath).resolve()
        if not any(str(path).startswith(str(base)) for base in cov_paths):
            continue

        executed_lines = set(line_counts)
        source_lines = _executable_lines(path)
        if not source_lines:
            continue

        missing_lines = sorted(line for line in source_lines if line not in executed_lines)
        covered_lines = len(source_lines) - len(missing_lines)
        coverage_percent = (covered_lines / len(source_lines)) * 100

        summary.append(
            {
                "path": path,
                "covered": covered_lines,
                "total": len(source_lines),
                "coverage_percent": coverage_percent,
                "missing": missing_lines,
            }
        )

    return sorted(summary, key=lambda item: str(item["path"]))


def _executable_lines(path):
    executable = []
    for idx, line in enumerate(linecache.getlines(path), 1):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            executable.append(idx)
    return executable


def _print_coverage(summary, reports):
    if not summary:
        print("\nNo trace coverage data collected.")
        return

    if any(report in {"term", "term-missing"} for report in reports):
        print("\nTrace coverage summary:")
        for entry in summary:
            missing_display = "".join(["; Missing lines: ", ", ".join(map(str, entry["missing"]))]) if entry["missing"] else ""
            print(
                f"{entry['path']}: {entry['coverage_percent']:.2f}% "
                f"({entry['covered']}/{entry['total']}){missing_display}"
            )


def _write_coverage_report(summary, report_path="trace_coverage_report.txt"):
    lines = ["Trace coverage report", "====================", ""]
    for entry in summary:
        missing_display = ", ".join(map(str, entry["missing"])) if entry["missing"] else "None"
        lines.append(
            f"{entry['path']}: {entry['coverage_percent']:.2f}% "
            f"({entry['covered']}/{entry['total']}) | Missing: {missing_display}"
        )

    Path(report_path).write_text("\n".join(lines))
