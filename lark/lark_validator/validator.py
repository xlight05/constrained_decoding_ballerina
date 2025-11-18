#!/usr/bin/env python3
"""
Lark Grammar Validator
Validates Lark grammar files by attempting to parse them with the Lark parser.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

from lark import Lark
from lark.exceptions import LarkError


class LarkGrammarValidator:
    """Validator for Lark grammar files."""
    
    def __init__(self, grammar_path: str):
        """
        Initialize the validator with a grammar file path.
        
        Args:
            grammar_path: Path to the Lark grammar file
        """
        self.grammar_path = Path(grammar_path)
        
    def validate_grammar(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the Lark grammar by attempting to instantiate a parser.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.grammar_path.exists():
            return False, f"Grammar file not found: {self.grammar_path}"
        
        try:
            with open(self.grammar_path, 'r', encoding='utf-8') as f:
                grammar_content = f.read()
            
            # Attempt to create a parser with the grammar
            parser = Lark(grammar_content, parser='earley')
            
            return True, None
            
        except LarkError as e:
            return False, f"Lark grammar error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def validate_with_test_input(self, test_input: str) -> Tuple[bool, Optional[str], Optional[object]]:
        """
        Validate the grammar and test it with sample input.
        
        Args:
            test_input: Sample input string to parse
            
        Returns:
            Tuple of (is_valid, error_message, parse_tree)
        """
        is_valid, error = self.validate_grammar()
        if not is_valid:
            return False, error, None
        
        try:
            with open(self.grammar_path, 'r', encoding='utf-8') as f:
                grammar_content = f.read()
            
            parser = Lark(grammar_content, parser='earley')
            parse_tree = parser.parse(test_input)
            
            return True, None, parse_tree
            
        except LarkError as e:
            return False, f"Parse error: {e}", None
        except Exception as e:
            return False, f"Unexpected error: {e}", None


def main():
    """Main entry point for the validator."""
    parser = argparse.ArgumentParser(
        description='Validate Lark grammar files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lark-validator spec.lark
  lark-validator spec.lark --test-input "import ballerina/io;"
  lark-validator spec.lark --test-file sample_input.txt
  lark-validator spec.lark --verbose
        """
    )
    
    parser.add_argument('grammar_file', help='Path to the Lark grammar file')
    parser.add_argument('--test-input', '-i', help='Test input string to parse')
    parser.add_argument('--test-file', '-f', help='File containing test input')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    validator = LarkGrammarValidator(args.grammar_file)
    
    print(f"Validating grammar: {args.grammar_file}")
    print("-" * 60)
    
    is_valid, error = validator.validate_grammar()
    
    if is_valid:
        print("✓ Grammar is valid!")
    else:
        print(f"✗ Grammar validation failed:")
        print(f"  {error}")
        sys.exit(1)
    
    # Test with input if provided
    test_input = None
    if args.test_input:
        test_input = args.test_input
    elif args.test_file:
        try:
            with open(args.test_file, 'r', encoding='utf-8') as f:
                test_input = f.read()
        except Exception as e:
            print(f"\n✗ Error reading test file: {e}")
            sys.exit(1)
    
    if test_input:
        print(f"\nTesting with input:")
        print("-" * 60)
        if args.verbose:
            print(test_input)
            print("-" * 60)
        
        is_valid, error, parse_tree = validator.validate_with_test_input(test_input)
        
        if is_valid:
            print("✓ Input parsed successfully!")
            if args.verbose and parse_tree:
                print("\nParse tree:")
                print(parse_tree.pretty())
        else:
            print(f"✗ Parsing failed:")
            print(f"  {error}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Validation complete!")


if __name__ == '__main__':
    main()
