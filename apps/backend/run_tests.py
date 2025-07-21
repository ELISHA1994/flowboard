#!/usr/bin/env python3
"""
Test runner script with various options for running tests.
"""
import sys
import subprocess
from typing import List, Optional


def run_command(cmd: List[str], description: str) -> int:
    """Run a command and return its exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd)
    return result.returncode


def run_all_tests():
    """Run all tests with coverage."""
    return run_command(["pytest"], "All tests with coverage")


def run_unit_tests():
    """Run only unit tests."""
    return run_command(
        ["pytest", "-m", "unit", "--cov-fail-under=0"], "Unit tests only"
    )


def run_integration_tests():
    """Run only integration tests."""
    return run_command(
        ["pytest", "-m", "integration", "--cov-fail-under=0"], "Integration tests only"
    )


def run_e2e_tests():
    """Run only end-to-end tests."""
    return run_command(
        ["pytest", "-m", "e2e", "--cov-fail-under=0"], "End-to-end tests only"
    )


def run_specific_file(file_path: str):
    """Run tests in a specific file."""
    return run_command(
        ["pytest", file_path, "-v", "--cov-fail-under=0"], f"Tests in {file_path}"
    )


def run_with_verbose():
    """Run all tests with verbose output."""
    return run_command(["pytest", "-vv", "-s"], "All tests with verbose output")


def run_failed_first():
    """Run failed tests first, then the rest."""
    return run_command(["pytest", "--failed-first"], "Failed tests first")


def run_last_failed():
    """Run only the tests that failed in the last run."""
    return run_command(["pytest", "--last-failed"], "Only last failed tests")


def generate_coverage_report():
    """Generate HTML coverage report."""
    run_command(
        ["pytest", "--cov=app", "--cov-report=html", "--cov-report=term"],
        "Generating coverage report",
    )
    print("\nCoverage report generated in htmlcov/index.html")
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("FastAPI Test Runner")
        print("===================")
        print("\nUsage: python run_tests.py [option]")
        print("\nOptions:")
        print("  all         - Run all tests with coverage")
        print("  unit        - Run unit tests only")
        print("  integration - Run integration tests only")
        print("  e2e         - Run end-to-end tests only")
        print("  verbose     - Run all tests with verbose output")
        print("  failed      - Run failed tests first")
        print("  last-failed - Run only last failed tests")
        print("  coverage    - Generate HTML coverage report")
        print("  file <path> - Run tests in specific file")
        print("\nExamples:")
        print("  python run_tests.py all")
        print("  python run_tests.py unit")
        print("  python run_tests.py file tests/unit/services/test_task_service.py")
        return 1

    option = sys.argv[1].lower()

    if option == "all":
        return run_all_tests()
    elif option == "unit":
        return run_unit_tests()
    elif option == "integration":
        return run_integration_tests()
    elif option == "e2e":
        return run_e2e_tests()
    elif option == "verbose":
        return run_with_verbose()
    elif option == "failed":
        return run_failed_first()
    elif option == "last-failed":
        return run_last_failed()
    elif option == "coverage":
        return generate_coverage_report()
    elif option == "file" and len(sys.argv) > 2:
        return run_specific_file(sys.argv[2])
    else:
        print(f"Unknown option: {option}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
