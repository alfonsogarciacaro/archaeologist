# Quick Tests

This directory contains standalone test files for rapid development and debugging. These are **not** part of the formal test suite - they're quick utilities for testing specific functionality in isolation.

## Files

### `test-context-menu.html`
**Purpose**: Standalone HTML file to test context menu styling and basic functionality
**Usage**: Open directly in browser to test context menu CSS and basic interactions
**Created for**: Debugging React Flow context menu positioning and styling issues

### `test-context-menu.js`
**Purpose**: Browser console script to test React Flow context menu integration
**Usage**: Run in browser console on the main application to test context menu behavior
**Created for**: Automated testing of context menu appearance and modal interactions

### `test_sequence.py`
**Purpose**: Direct database testing script for SQLite auto-increment sequence behavior
**Usage**: Run from command line to test database ID sequence after deletions
**Created for**: Debugging suspected SQLite sequence reuse issue (turned out to be frontend duplicate filtering)

## Usage Guidelines

### When to Use These Files
- **Rapid debugging**: Test specific functionality without full test suite overhead
- **Isolation testing**: Verify components work independently
- **Development tools**: Quick utilities during feature development
- **Issue reproduction**: Create minimal test cases for bugs

### When NOT to Use These Files
- **CI/CD pipelines**: Use formal test suite instead
- **Production verification**: Use proper integration tests
- **Comprehensive testing**: These are targeted, not exhaustive

## Running the Tests

### Context Menu Tests
```bash
# Basic styling test
open quick_tests/test-context-menu.html

# Integration test (run in browser console on main app)
# Copy-paste contents of test-context-menu.js
```

### Database Sequence Test
```bash
# From project root
python quick_tests/test_sequence.py
```

## Notes

- These files are **development utilities**, not production tests
- They may contain hardcoded paths and assumptions
- Feel free to modify, extend, or remove as needed
- Add new quick test files here for future debugging needs

## Integration with Formal Tests

If any of these quick tests become valuable for long-term verification, consider:
1. Moving them to the appropriate `tests/` directory
2. Converting them to proper unit/integration tests
3. Adding them to CI/CD pipeline
4. Updating them to use proper test frameworks and fixtures