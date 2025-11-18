/**
 * Type definitions for the Ballerina GBNF Validator
 */

import { ParseState, RuleType, type Rule } from 'gbnf';

/**
 * Result of validation operation
 */
export interface ValidationResult {
  valid: boolean;
  message: string;
  position?: number;
  error?: Error;
}

/**
 * Re-export GBNF types
 */
export type { ParseState, Rule };
export { RuleType };

/**
 * Options for the validator
 */
export interface ValidatorOptions {
  verbose?: boolean;
  throwOnError?: boolean;
}
