#!/usr/bin/env python3
"""
Test case for structured JSON export functionality

This test verifies that the tracer can correctly export trace data
in the structured JSON format with token probabilities.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parser import GrammarTraceParser
from exporter import TraceExporter


class TestStructuredJSONExport(unittest.TestCase):
    """Test cases for structured JSON export"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures - use the real trace file"""
        cls.trace_file = Path(__file__).parent.parent / "traces" / "trace_test.json"

        if not cls.trace_file.exists():
            raise FileNotFoundError(
                f"Trace file not found: {cls.trace_file}\n"
                "Please ensure traces/trace_test.json exists before running tests."
            )

    def test_export_structured_json_creates_valid_format(self):
        """Test that export creates valid JSON in the expected format"""
        # Parse the trace file
        parser = GrammarTraceParser()
        trace = parser.parse_trace_file(str(self.trace_file))

        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exporter = TraceExporter()
            result = exporter.export_structured_json(trace, output_path, top_k=5)

            # Verify file was created
            self.assertTrue(os.path.exists(output_path), "Output file should exist")

            # Load and verify JSON is valid
            with open(output_path, 'r') as f:
                data = json.load(f)

            # Verify structure
            self.assertIsInstance(data, list, "Output should be a list")
            self.assertGreater(len(data), 0, "Output should contain steps")

            # Verify first step has correct structure
            first_step = data[0]
            self.assertIn("step", first_step, "Step should have 'step' field")
            self.assertIn("accepted_token", first_step, "Step should have 'accepted_token' field")
            self.assertIn("accepted_probability", first_step, "Step should have 'accepted_probability' field")
            self.assertIn("all_tokens", first_step, "Step should have 'all_tokens' field")

            # Verify all_tokens structure
            all_tokens = first_step["all_tokens"]
            self.assertIsInstance(all_tokens, list, "all_tokens should be a list")
            self.assertGreater(len(all_tokens), 0, "all_tokens should not be empty")

            # Verify token structure
            first_token = all_tokens[0]
            self.assertIn("token", first_token, "Token should have 'token' field")
            self.assertIn("probability", first_token, "Token should have 'probability' field")

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_accepted_token_has_valid_probability(self):
        """Test that accepted tokens have valid (non-zero) probabilities"""
        parser = GrammarTraceParser()
        trace = parser.parse_trace_file(str(self.trace_file))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exporter = TraceExporter()
            exporter.export_structured_json(trace, output_path, top_k=5)

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Check that accepted tokens have valid probabilities
            steps_with_valid_probs = 0
            for step_data in data:
                accepted_prob = step_data["accepted_probability"]

                # Probability should be between 0 and 1
                self.assertGreaterEqual(
                    accepted_prob, 0.0,
                    f"Step {step_data['step']}: Probability should be >= 0"
                )
                self.assertLessEqual(
                    accepted_prob, 1.0,
                    f"Step {step_data['step']}: Probability should be <= 1"
                )

                # Count steps with valid (non-zero) probabilities
                if accepted_prob > 0:
                    steps_with_valid_probs += 1

            # At least some steps should have valid probabilities
            self.assertGreater(
                steps_with_valid_probs, 0,
                "At least some steps should have non-zero probabilities"
            )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_probabilities_sum_to_approximately_one(self):
        """Test that probabilities in all_tokens sum to approximately 1.0"""
        parser = GrammarTraceParser()
        trace = parser.parse_trace_file(str(self.trace_file))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exporter = TraceExporter()
            # Use larger top_k to better test probability sum
            exporter.export_structured_json(trace, output_path, top_k=20)

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Check probability sums for steps with multiple candidates
            for step_data in data:
                all_tokens = step_data["all_tokens"]

                # Only check steps with multiple candidates
                if len(all_tokens) > 1:
                    prob_sum = sum(t["probability"] for t in all_tokens)

                    # Sum should be close to 1.0 (allow some tolerance for rounding)
                    self.assertLessEqual(
                        prob_sum, 1.0001,
                        f"Step {step_data['step']}: Probability sum {prob_sum} should not exceed 1.0"
                    )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_top_k_parameter_limits_alternatives(self):
        """Test that top_k parameter correctly limits the number of alternatives"""
        parser = GrammarTraceParser()
        trace = parser.parse_trace_file(str(self.trace_file))

        for top_k in [3, 5, 10]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_path = f.name

            try:
                exporter = TraceExporter()
                exporter.export_structured_json(trace, output_path, top_k=top_k)

                with open(output_path, 'r') as f:
                    data = json.load(f)

                # Verify that steps don't have more than top_k alternatives
                for step_data in data:
                    all_tokens = step_data["all_tokens"]
                    self.assertLessEqual(
                        len(all_tokens), top_k,
                        f"Step {step_data['step']}: Should have at most {top_k} tokens, got {len(all_tokens)}"
                    )

            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_specific_trace_content(self):
        """Test specific content from the trace file"""
        parser = GrammarTraceParser()
        trace = parser.parse_trace_file(str(self.trace_file))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exporter = TraceExporter()
            exporter.export_structured_json(trace, output_path, top_k=5)

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Based on the trace file, we expect:
            # - Step 1 should have "import" as accepted token
            # - The generated text should contain ballerina code

            # Find step 1
            step_1 = next((s for s in data if s["step"] == 1), None)
            self.assertIsNotNone(step_1, "Step 1 should exist")
            self.assertEqual(
                step_1["accepted_token"], "import",
                "Step 1 should have 'import' as accepted token"
            )

            # Verify step 1 has a high probability for "import"
            self.assertGreater(
                step_1["accepted_probability"], 0.5,
                "Step 1 'import' should have high probability (grammar filtered)"
            )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_all_tokens_sorted_by_probability(self):
        """Test that all_tokens list is sorted by probability in descending order"""
        parser = GrammarTraceParser()
        trace = parser.parse_trace_file(str(self.trace_file))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exporter = TraceExporter()
            exporter.export_structured_json(trace, output_path, top_k=10)

            with open(output_path, 'r') as f:
                data = json.load(f)

            # Verify sorting for each step
            for step_data in data:
                all_tokens = step_data["all_tokens"]

                if len(all_tokens) > 1:
                    # Check that probabilities are in descending order
                    probs = [t["probability"] for t in all_tokens]
                    sorted_probs = sorted(probs, reverse=True)

                    self.assertEqual(
                        probs, sorted_probs,
                        f"Step {step_data['step']}: Tokens should be sorted by probability"
                    )

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


def main():
    """Run the test suite"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStructuredJSONExport)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
