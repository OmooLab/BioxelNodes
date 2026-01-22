# BioxelNodes Unit Tests

This directory contains unit tests for the bioxel module.

## Test Data

Test files should be placed in `tests/data/`:

## Running Tests

Run all tests:
```bash
uv run pytest
```

Run specific test file:
```bash
uv run pytest tests/test_bioxel.py
```

Run specific test class:
```bash
uv run pytest tests/test_bioxel.py::TestDataClass
```

Run with verbose output:
```bash
uv run pytest -v
```

Run with coverage:
```bash
uv run pytest --cov=bioxelnodes.bioxel --cov-report=html
```

## Test Categories

- **TestDataClass**: Data class initialization and properties
- **TestDataToLayers**: Data.to_layers() method
- **TestUtilityFunctions**: Utility functions
- **TestLayerClass**: Layer class functionality
- **TestConstants**: Module constants
- **TestEdgeCases**: Edge cases and error handling
