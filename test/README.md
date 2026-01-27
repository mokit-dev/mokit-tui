# MOKIT TUI Test Suite

This directory contains comprehensive tests for the MOKIT TUI application, particularly focusing on the updated energy parsing functionality.

## Test Files

### Core Tests

- **`test_energy_parsing.py`** - Unit tests for energy parsing functionality
  - Tests MRSF-CIS and SA-CAS section header detection
  - Tests state line parsing for both formats
  - Tests complete file parsing with mixed energy formats
  - Tests edge cases and error conditions

- **`test_integration.py`** - Integration tests for realistic scenarios
  - Tests with realistic CH2 calculation output
  - Tests multiple sections in the same file
  - Tests performance with large files
  - Tests unicode and special character handling

- **`run_tests.py`** - Test runner script
  - Runs all tests with detailed output
  - Can run specific test modules
  - Provides success/failure reporting

## Running Tests

### Run All Tests
```bash
cd /home/wsr/tui
python test/run_tests.py
```

### Run Specific Test File
```bash
python test/run_tests.py test_energy_parsing
python test/run_tests.py test_integration
```

### Run Tests Manually
```bash
python -m pytest test/ -v  # If pytest is available
python -m unittest discover test/ -v  # Standard library
```

### Run Individual Test Files
```bash
python test/test_energy_parsing.py
python test/test_integration.py
```

## Test Coverage

The test suite covers:

### Energy Parsing Features
- ✅ MRSF-CIS section header detection
- ✅ SA-CAS section header detection  
- ✅ State line parsing for both formats
- ✅ Header inclusion in output
- ✅ Mixed energy format handling
- ✅ Regular energy patterns (E(RHF), E(UHF), etc.)

### Edge Cases
- ✅ Files with no energy information
- ✅ Headers with no state lines
- ✅ Malformed state lines
- ✅ Unicode and special characters
- ✅ Large file performance

### Integration Scenarios
- ✅ Realistic quantum chemistry output
- ✅ Multiple sections of same type
- ✅ Mixed content types
- ✅ Error handling

## Adding New Tests

When adding new energy formats or parser features:

1. Add unit tests to `test_energy_parsing.py`
2. Add integration tests to `test_integration.py`  
3. Test both happy path and edge cases
4. Verify error handling for malformed input
5. Test performance with large inputs

## Test Data

Test files are created in temporary directories during test execution and cleaned up automatically. No external test data files are required.

## Dependencies

The tests use only Python standard library modules:
- `unittest` - Testing framework
- `pathlib` - Path handling
- `tempfile` - Temporary file creation
- `sys` - System operations

No additional dependencies are required.