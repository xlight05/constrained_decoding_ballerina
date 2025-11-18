import * as fs from 'fs';
import * as path from 'path';
import { ValidationResult, ParseState, RuleType, ValidatorOptions } from './types.js';

/**
 * BallerinaValidator class for validating Ballerina code against GBNF grammar
 */
export class BallerinaValidator {
  private grammarText: string;
  private options: ValidatorOptions;

  constructor(grammarText: string, options: ValidatorOptions = {}) {
    this.grammarText = grammarText;
    this.options = {
      verbose: options.verbose ?? false,
      throwOnError: options.throwOnError ?? false,
    };
  }

  /**
   * Load grammar from file
   */
  static fromFile(grammarPath: string, options?: ValidatorOptions): BallerinaValidator {
    const grammarText = fs.readFileSync(grammarPath, 'utf-8');
    return new BallerinaValidator(grammarText, options);
  }

  /**
   * Validate input text against the loaded grammar
   */
  async validate(input: string): Promise<ValidationResult> {
    try {
      // Dynamically import gbnf (ESM module)
      const GBNF = (await import('gbnf')).default;

      // Log grammar if verbose
      if (this.options.verbose) {
        console.log('Grammar:');
        console.log(this.grammarText);
        console.log('\nValidating input:');
        console.log(input);
        console.log();
      }

      // Create grammar state
      let state: ParseState;
      try {
        state = GBNF(this.grammarText);
      } catch (error) {
        return {
          valid: false,
          message: `Invalid grammar: ${error instanceof Error ? error.message : String(error)}`,
          error: error instanceof Error ? error : new Error(String(error)),
        };
      }

      // Validate input character by character
      let position = 0;
      try {
        for (const char of input) {
          state = state.add(char);
          position++;

          if (this.options.verbose) {
            console.log(`Position ${position}: '${char}' - Valid`);
          }
        }

        // Check if we're at a valid end state
        const rules = [...state];
        const hasEndRule = rules.some((rule) => rule.type === RuleType.END);

        if (hasEndRule) {
          return {
            valid: true,
            message: 'Input is valid according to the grammar',
          };
        } else {
          return {
            valid: false,
            message: `Input is incomplete. Expected more content after position ${position}`,
            position,
          };
        }
      } catch (error) {
        return {
          valid: false,
          message: `Invalid input at position ${position}: ${
            error instanceof Error ? error.message : String(error)
          }`,
          position,
          error: error instanceof Error ? error : new Error(String(error)),
        };
      }
    } catch (error) {
      if (this.options.throwOnError) {
        throw error;
      }
      return {
        valid: false,
        message: `Validation error: ${error instanceof Error ? error.message : String(error)}`,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }

  /**
   * Validate a file
   */
  async validateFile(filePath: string): Promise<ValidationResult> {
    try {
      const input = fs.readFileSync(filePath, 'utf-8');
      return await this.validate(input);
    } catch (error) {
      return {
        valid: false,
        message: `Error reading file: ${error instanceof Error ? error.message : String(error)}`,
        error: error instanceof Error ? error : new Error(String(error)),
      };
    }
  }
}
