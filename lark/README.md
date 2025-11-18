# Lark Grammar Validator

A Python tool to validate Lark grammar files.

## Installation

### Using pip (recommended)

```bash
cd lark
pip install -e .
```

### Using uv (fast)

```bash
cd lark
uv pip install -e .
```

### Using Poetry

```bash
cd lark
poetry install
```

## Usage

After installation, use the `lark-validator` command:

```bash
# Validate grammar syntax
lark-validator spec.lark

# Validate and test with input string
lark-validator spec.lark --test-input "import ballerina/io;"

# Validate and test with input from file
lark-validator spec.lark --test-file sample_input.txt

# Verbose output with parse tree
lark-validator spec.lark --test-file sample_input.txt --verbose
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Project Structure

```
lark/
├── pyproject.toml          # Project configuration
├── lark_validator/
│   ├── __init__.py
│   └── validator.py        # Main validator code
├── spec.lark               # Grammar file to validate
└── sample_input.txt        # Sample test input
```
