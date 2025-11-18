# Contributing to the Ballerina Lark Grammar

This document provides guidelines for extending the Lark grammar for Ballerina, specifically optimized for **constrained decoding** with LLMs using llguidance.

## Table of Contents

- [Overview](#overview)
- [Key Constraints for Constrained Decoding](#key-constraints-for-constrained-decoding)
- [Adding New Rules](#adding-new-rules)
- [Testing Your Changes](#testing-your-changes)
- [Common Pitfalls](#common-pitfalls)

---

## Overview

This grammar is used with [llguidance](https://github.com/guidance-ai/llguidance) to constrain LLM output to valid Ballerina syntax. Unlike traditional parsing where the grammar validates existing text, constrained decoding uses the grammar to **guide text generation** token by token.

This fundamental difference means some common grammar patterns that work perfectly for parsing will cause issues during generation.

---

## Key Constraints for Constrained Decoding

### 1. ❌ Do NOT Use `%ignore WS`

**Problem**: Using `%ignore WS` makes whitespace optional during parsing, which is fine. However, during **generation**, this means the LLM can generate tokens without any whitespace between them.

**Example of the issue**:
```lark
# BAD - tokens will concatenate
WS: /[ \t\n\r]+/
%ignore WS

start: IMPORT IDENTIFIER ";" FUNCTION IDENTIFIER
```

**Generated output**: `importballerina;functionmain` (no spaces!)

**Reason**: `%ignore` tells the grammar that whitespace is allowed but not required between tokens. The LLM's probability distribution doesn't inherently prefer spaces, so it generates the most likely next token without inserting whitespace.

**Solution**: Explicitly include whitespace terminals in your rules:
```lark
# GOOD - whitespace is explicit
SP: / +/              # Required space
NL: /[\n][ ]*/        # Newline with optional indentation

start: IMPORT SP IDENTIFIER ";" NL FUNCTION SP IDENTIFIER
```

---

### 2. ✅ Alternatives ARE Safe When Starting with Different Keywords

**Key Insight**: Alternatives are **perfectly fine** when each branch starts with a **distinct keyword**. The LLM can correctly choose based on semantic context.

**Example - This WORKS:**
```lark
# GOOD - Each alternative starts with a different keyword
statement: foreach_stmt     # starts with "foreach"
         | while_stmt       # starts with "while"
         | if_stmt          # starts with "if"
         | return_stmt      # starts with "return"
         | var_decl_stmt    # starts with type keyword (int/string/var)
         | call_stmt        # starts with IDENTIFIER

foreach_stmt: FOREACH SP ...
while_stmt: WHILE SP ...
if_stmt: IF SP ...
```

**Why this works**: When the LLM needs to generate a statement, it uses semantic context from the prompt. If asked to "loop through numbers", it naturally generates "foreach" or "while". If asked to "print hello world", it generates a simple call statement.

### ❌ Problematic: Alternatives Starting with the SAME Token

Problems arise when alternatives begin with the **same token type**:

```lark
# BAD - Both start with IDENTIFIER
expression_stmt: function_call     # IDENTIFIER "(" ...
               | assignment        # IDENTIFIER "=" ...
```

**Solution**: Restructure so disambiguation happens after the common prefix:
```lark
# BETTER - Shared prefix, late disambiguation
expression_stmt: IDENTIFIER "(" arg_list ")" ";"      # call
               | IDENTIFIER SP "=" SP expression ";"  # assignment
```

---

### 3. ✅ Define Keywords Before IDENTIFIER

**Reason**: Lark gives priority to terminals defined earlier in the file. If `IDENTIFIER` is defined before keywords, it might match keywords as identifiers.

```lark
# GOOD - keywords first
FOREACH: "foreach"
IN: "in"
PUBLIC: "public"
FUNCTION: "function"

# IDENTIFIER comes after keywords
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
```

---

### 4. ✅ Use Explicit Whitespace Terminals

Define specific whitespace terminals for different contexts:

```lark
SP: / +/              # One or more spaces (same line)
NL: /[\n][ ]*/        # Newline followed by optional indentation
```

- Use `SP` between tokens that should be on the same line
- Use `NL` for line breaks and statement separation

---

## Adding New Rules

### Step 1: Identify the Ballerina Spec Production

Find the relevant production in the [Ballerina Language Specification](https://ballerina.io/spec/lang/2019R3/). For example:

```
while-stmt := 'while' expression block-stmt
```

### Step 2: Determine the Nesting Level

Decide where this statement type belongs in the hierarchy:
- **Main level**: Statements in the function body (e.g., `foreach`, `while`, `if`)
- **Inner level**: Statements inside blocks (e.g., `call_stmt`, `return`)

### Step 3: Write the Rule with Explicit Whitespace

```lark
# Adding while statement at main level
main_statement: foreach_stmt
              | while_stmt      # Add new alternative ONLY if necessary

while_stmt: WHILE SP expression SP block_stmt
```

### Step 4: If Adding Alternatives is Unavoidable

If you must add alternatives at the same level, consider:

1. **Make them syntactically distinguishable early**:
   ```lark
   # Better - different keywords at start
   main_statement: foreach_stmt    # starts with "foreach"
                 | while_stmt      # starts with "while"
   ```

2. **Avoid alternatives that start with the same token type**:
   ```lark
   # BAD - both start with IDENTIFIER
   statement: function_call    # IDENTIFIER "(" ...
            | assignment       # IDENTIFIER "=" ...
   ```

3. **Test thoroughly** with the constrained decoding to verify behavior.

### Step 5: Add Required Terminals

If your rule needs new keywords:

```lark
# Add at the TOP of the file, before IDENTIFIER
WHILE: "while"
BREAK: "break"
CONTINUE: "continue"
```

---

## Testing Your Changes

### 1. Validate Grammar Syntax

```bash
cd /path/to/lark
python3 -m lark_validator.validator spec.lark --verbose
```

### 2. Test with Sample Input

```bash
python3 -m lark_validator.validator spec.lark --test-file sample_input.txt --verbose
```

### 3. Test with Constrained Decoding

```bash
cd /path/to/invoker
bal run
```

Check that:
- Output has proper whitespace and formatting
- The correct statement types are generated (not just the simplest alternative)
- The output is valid Ballerina syntax

### 4. Test Edge Cases with curl

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Your test prompt"}],
    "grammar": "%llguidance {}\n... your grammar ...",
    "max_tokens": 100,
    "temperature": 0
  }'
```

---

## Common Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| Using `%ignore WS` | Tokens concatenate: `importballerina` | Use explicit `SP` and `NL` terminals |
| Same-token alternatives | LLM biased to one branch | Ensure alternatives start with different keywords |
| IDENTIFIER before keywords | Keywords parsed as identifiers | Define keywords first |
| Zero-width regex | Lark error: "Dynamic Earley doesn't allow zero-width regexps" | Use `+` instead of `*` for required whitespace |
| Unbounded repetition | LLM generates infinite content | Limit repetition (e.g., single import) |
| Over-constrained grammar | Same output for all prompts | Add alternatives with distinct keywords |
| Missing trailing whitespace | Parse error at end of file | Add `NL?` at end of `start` rule |

---

## Example: Adding a While Statement

Here's a complete example of adding `while` support:

```lark
# 1. Add keyword (at top, before IDENTIFIER)
WHILE: "while"

# 2. Add to statement alternatives (safe - starts with different keyword)
statement: foreach_stmt
         | while_stmt
         | call_stmt

# 3. Define the rule with explicit whitespace
while_stmt: WHILE SP expression SP block

# 4. Ensure block is defined
block: "{" NL statement_list "}"
```

---

## Reference: Current Grammar Structure

```
start
└── module_part
    ├── import_decl (single import)
    └── function_defn
        └── function_body
            └── statement_list
                └── statement (LLM CHOOSES based on prompt context)
                    ├── foreach_stmt  → starts with "foreach"
                    ├── while_stmt    → starts with "while"
                    ├── if_stmt       → starts with "if"
                    ├── return_stmt   → starts with "return"
                    ├── var_decl_stmt → starts with type keyword
                    └── call_stmt     → starts with IDENTIFIER
```

This structure ensures:
- Each statement type starts with a distinguishable token
- The LLM can choose appropriate constructs based on prompt semantics
- All generated code is syntactically valid Ballerina

---

## Questions?

If you encounter issues with constrained decoding that aren't covered here, test with simplified grammars to isolate the problem, then document your findings in this guide.
