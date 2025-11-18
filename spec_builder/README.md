# Note: Completely Vibe Coded Project: Just a POC.

# Ballerina GBNF Validator

A TypeScript-based validator for Ballerina code using GBNF (Grammar BNF) specification. This tool validates Ballerina source files against a formal grammar definition.

## Overview

This project provides:
- **GBNF Grammar Specification** (`grammars/spec.gbnf`) - A minimal grammar for Ballerina language constructs
- **TypeScript Validator** - Validates Ballerina files against the GBNF spec using the [gbnf](https://gbnf.dev) library
- **CLI Tool** - Command-line interface for easy validation

## Features

- ✅ Validates Ballerina function definitions
- ✅ Supports `foreach` loops with range expressions
- ✅ Character-by-character validation with detailed error reporting
- ✅ Verbose mode for debugging
- ✅ Type-safe TypeScript implementation

## Installation

```bash
npm install
```

## Usage

### Basic Validation

Validate a Ballerina file:

```bash
npm run validate main.bal
```

### Verbose Mode

Show detailed character-by-character validation:

```bash
node dist/index.js main.bal --verbose
```

### Help

Display usage information:

```bash
node dist/index.js --help
```

## Project Structure

```
spec_builder/
├── src/
│   ├── index.ts          # CLI entry point
│   ├── validator.ts      # Core validation logic
│   └── types.ts          # TypeScript type definitions
├── grammars/
│   └── spec.gbnf         # Ballerina GBNF grammar specification
├── dist/                 # Compiled JavaScript output
├── main.bal              # Sample Ballerina file for testing
├── package.json
├── tsconfig.json
└── README.md
```

## Grammar Coverage

The current GBNF specification (`grammars/spec.gbnf`) supports:

- **Function Definitions**: `public function` declarations
- **Foreach Loops**: `foreach int i in 0...9 { ... }`
- **Range Expressions**: `0...9` syntax
- **Type Descriptors**: `int`, `string`, `float`, `boolean`, `var`
- **Identifiers**: Variable and function names
- **Whitespace**: Spaces, tabs, newlines

### Example Valid Ballerina Code

```ballerina
public function main() {
    foreach int i in 0...9 {

    }
}
```

## Development

### Build

Compile TypeScript to JavaScript:

```bash
npm run build
```

### Clean

Remove compiled output:

```bash
npm run clean
```

### Scripts

- `npm run build` - Compile TypeScript
- `npm run validate` - Build and validate main.bal
- `npm run start` - Build and run CLI
- `npm run dev` - Quick compile and run
- `npm run clean` - Remove dist folder

## How It Works

1. **Grammar Definition**: The GBNF grammar in `grammars/spec.gbnf` defines the syntax rules for Ballerina code
2. **Parser**: The [gbnf](https://www.npmjs.com/package/gbnf) library parses the grammar and creates a state machine
3. **Validation**: Input is validated character-by-character against the grammar state machine
4. **Result**: Returns success or detailed error with position information

## API

### BallerinaValidator Class

```typescript
import { BallerinaValidator } from './validator.js';

// Create from grammar string
const validator = new BallerinaValidator(grammarText, { verbose: false });

// Create from grammar file
const validator = BallerinaValidator.fromFile('./grammars/spec.gbnf');

// Validate text
const result = await validator.validate(ballerinaCode);

// Validate file
const result = await validator.validateFile('./main.bal');
```

### ValidationResult

```typescript
interface ValidationResult {
  valid: boolean;        // Whether input is valid
  message: string;       // Success or error message
  position?: number;     // Error position (if invalid)
  error?: Error;         // Error object (if any)
}
```

## Extending the Grammar

To add support for more Ballerina language features:

1. Edit `grammars/spec.gbnf` to add new grammar rules
2. Follow GBNF syntax (see [GBNF Documentation](https://gbnf.dev/docs/))
3. Rebuild and test: `npm run build && npm run validate`

### GBNF Syntax Reference

```gbnf
# Literal strings
rule ::= "exact text"

# Character classes
rule ::= [a-zA-Z0-9]

# Optional (?)
rule ::= item?

# Zero or more (*)
rule ::= item*

# One or more (+)
rule ::= item+

# Alternatives (|)
rule ::= option1 | option2

# Grouping
rule ::= (item1 | item2) item3
```

## Dependencies

- [gbnf](https://www.npmjs.com/package/gbnf) - GBNF grammar parser and validator
- [typescript](https://www.typescriptlang.org/) - TypeScript compiler
- [@types/node](https://www.npmjs.com/package/@types/node) - Node.js type definitions

## References

- [Ballerina Specification v2019R3](https://htmlpreview.github.io/?https://raw.githubusercontent.com/ballerina-platform/ballerina-spec/v2019R3/lang/spec.html)
- [GBNF Documentation](https://gbnf.dev/docs/)
- [GBNF npm Package](https://www.npmjs.com/package/gbnf)

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### "Invalid grammar" error

Check that your GBNF syntax is correct. Common issues:
- Missing whitespace rules (`ws`)
- Circular references without terminals
- Invalid regex patterns in character classes

### "Invalid input at position X" error

The input doesn't match the grammar at character position X. Use verbose mode to see validation progress:

```bash
node dist/index.js main.bal --verbose
```

### Build errors

Ensure you're using Node.js 16+ and have all dependencies installed:

```bash
node --version
npm install
```
