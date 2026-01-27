#!/usr/bin/env python3
"""
Test runner for MOKIT TUI test suite.
Run all tests and generate coverage reports.
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_tests():
    """Run all tests in the test directory"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test module"""
    try:
        suite = unittest.TestLoader().loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"Error loading test {test_name}: {e}")
        return False


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        print(f"Running specific test: {test_name}")
        success = run_specific_test(test_name)
    else:
        # Run all tests
        print("Running MOKIT TUI test suite...")
        print("=" * 60)
        success = run_tests()

    print("=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
