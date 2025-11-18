#!/usr/bin/env node

import * as path from 'path';
import { fileURLToPath } from 'url';
import { BallerinaValidator } from './validator.js';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * CLI tool for validating Ballerina files against GBNF grammar
 */
async function main() {
  const args = process.argv.slice(2);

  // Show usage if no arguments
  if (args.length === 0) {
    console.log('Ballerina GBNF Validator');
    console.log('========================\n');
    console.log('Usage: npm run validate <file.bal> [options]\n');
    console.log('Options:');
    console.log('  -v, --verbose    Show verbose output');
    console.log('  -h, --help       Show this help message\n');
    console.log('Example:');
    console.log('  npm run validate main.bal');
    console.log('  npm run validate main.bal --verbose');
    process.exit(0);
  }

  // Parse arguments
  const flags = args.filter((arg) => arg.startsWith('-'));
  const files = args.filter((arg) => !arg.startsWith('-'));

  if (flags.includes('-h') || flags.includes('--help')) {
    console.log('Ballerina GBNF Validator');
    console.log('========================\n');
    console.log('Usage: npm run validate <file.bal> [options]\n');
    console.log('Options:');
    console.log('  -v, --verbose    Show verbose output');
    console.log('  -h, --help       Show this help message\n');
    console.log('Example:');
    console.log('  npm run validate main.bal');
    console.log('  npm run validate main.bal --verbose');
    process.exit(0);
  }

  if (files.length === 0) {
    console.error('Error: No input file specified');
    console.error('Usage: npm run validate <file.bal>');
    process.exit(1);
  }

  const verbose = flags.includes('-v') || flags.includes('--verbose');
  const inputFile = files[0];

  // Resolve paths
  const grammarPath = path.join(__dirname, '../grammars/spec.gbnf');
  const inputPath = path.resolve(inputFile);

  console.log(`Validating: ${inputPath}`);
  console.log(`Grammar: ${grammarPath}\n`);

  try {
    // Create validator
    const validator = BallerinaValidator.fromFile(grammarPath, { verbose });

    // Validate the file
    const result = await validator.validateFile(inputPath);

    // Display results
    if (result.valid) {
      console.log('✓ Valid Ballerina code');
      console.log(`  ${result.message}`);
      process.exit(0);
    } else {
      console.error('✗ Invalid Ballerina code');
      console.error(`  ${result.message}`);
      if (result.position !== undefined) {
        console.error(`  Error at position: ${result.position}`);
      }
      if (result.error && verbose) {
        console.error('\nError details:');
        console.error(result.error);
      }
      process.exit(1);
    }
  } catch (error) {
    console.error('Fatal error:', error instanceof Error ? error.message : String(error));
    if (verbose && error instanceof Error && error.stack) {
      console.error('\nStack trace:');
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run the CLI
main().catch((error) => {
  console.error('Unexpected error:', error);
  process.exit(1);
});
