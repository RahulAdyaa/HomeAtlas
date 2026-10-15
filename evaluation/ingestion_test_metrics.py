"""Metric arithmetic tests; never alter frozen fixture gold."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('ingestion_eval', Path(__file__).with_name('ingestion_eval.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IngestionMetricTests(unittest.TestCase):
    def test_error_counts_include_missing_evidence(self):
        self.assertEqual(module.error_counts('A B', '')['word_edits'], 2)
        self.assertEqual(module.error_counts('A B', '')['reference_words'], 2)

    def test_case_and_whitespace_normalization_preserve_punctuation(self):
        self.assertEqual(module.normalized('Ａ\n  B.'), 'a b.')
        self.assertEqual(module.error_counts('A b.', 'a b')['character_edits'], 1)

    def test_whole_tokens_and_contiguous_phrase(self):
        self.assertFalse(module.contains('30 months', '3'))
        self.assertTrue(module.contains('Power W\nCost USD', 'Cost USD'))
        self.assertFalse(module.contains('INLET HEPA MESH FAN', 'MESH HEPA'))

    def test_edit_distance_and_quantile(self):
        self.assertEqual(module.edit_distance('kitten', 'sitting'), 3)
        self.assertEqual(module.quantile([1, 2, 3, 4], .5), 2.5)


if __name__ == '__main__':
    unittest.main()
