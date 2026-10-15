"""Statistical arithmetic and fail-closed orchestration tests; synthetic numbers only."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import stats_analysis as sa
from run_eval import selected_groups


class StatisticsTests(unittest.TestCase):
    def test_question_clusters_do_not_double_denominator(self):
        samples = [[{'id': 'a', 'value': 0.}, {'id': 'b', 'value': 1.}],
                   [{'id': 'a', 'value': 0.}, {'id': 'b', 'value': 1.}]]
        result = sa.bootstrap_interval(samples, draws=200)
        self.assertEqual(result['n_clusters'], 2)
        self.assertEqual(result['n_observations'], 4)
        self.assertEqual(result['low'], 0.)
        self.assertEqual(result['high'], 1.)

    def test_seeded_bootstrap_is_reproducible(self):
        samples = [[{'id': str(i), 'value': i/10} for i in range(6)]]
        self.assertEqual(sa.bootstrap_interval(samples, draws=200), sa.bootstrap_interval(samples, draws=200))

    def test_duplicate_sample_ids_fail_closed(self):
        samples = [[{'id': 'a', 'value': 0}, {'id': 'a', 'value': 1}]]
        self.assertEqual(sa.bootstrap_interval(samples, draws=200)['status'], 'NOT MEASURED')

    def test_wrong_sample_denominator_has_no_ci(self):
        run = {'metrics': [{'metric': 'x', 'value': .5, 'n': 3}], 'phase': 'baseline', 'run': 1,
               'statistic_samples': {'x': [{'id': 'a', 'value': 0}, {'id': 'b', 'value': 1}]}}
        sources = {agent: {'payload': {'runs': [run, {**run, 'run': 2}]}} for agent in sa.INFERENCE_AGENTS}
        with patch.object(sa, 'metric_samples', return_value=(run['statistic_samples']['x'], 'mean')):
            rows = sa.aggregate_metrics(sources, 'baseline', 200)
        self.assertTrue(all(r['ci95']['status'] == 'NOT MEASURED' for r in rows))
        self.assertEqual(rows[0]['value'], .5)

    def test_missing_judge_is_not_zero(self):
        run = {'metrics': [{'metric': 'faithfulness', 'value': None, 'n': 60, 'reason': 'No judge'}],
               'phase': 'baseline', 'run': 1}
        sources = {agent: {'payload': {'runs': [run, {**run, 'run': 2}]}} for agent in sa.INFERENCE_AGENTS}
        rows = sa.aggregate_metrics(sources, 'baseline', 200)
        self.assertTrue(all(r['value'] is None and r['status'] == 'NOT MEASURED' for r in rows))

    def test_best_single_can_outperform_hybrid(self):
        rows = []
        for i in range(8):
            metrics = {variant: {'5': {field: value for field in ['precision', 'recall', 'mrr', 'ndcg']}}
                       for variant, value in [('dense', .2), ('word', .4), ('fuzzy', 1.), ('hybrid_runtime', .5)]}
            rows.append({'id': str(i), 'gold_ids': ['gold'], 'subset': 'typo', 'metrics': metrics})
        runs = [{'phase': 'baseline', 'run': number, 'per_question': rows} for number in [1, 2]]
        tests = sa.paired_significance({'retrieval-agent': {'payload': {'runs': runs}}}, 'baseline', 200, 200)
        self.assertEqual(len(tests), 8)
        self.assertTrue(all(t['best_single'] == 'fuzzy' for t in tests))
        self.assertTrue(all(t['difference'] == -.5 for t in tests))
        self.assertTrue(all(not t['hybrid_significantly_better_at_05'] for t in tests))
        self.assertTrue(all(t['n'] == 8 for t in tests))

    def test_group_aliases_preserve_order_without_duplicates(self):
        self.assertEqual(selected_groups(['A,G', 'F', 'L']), ['retrieval', 'ingestion', 'stats'])

    def test_missing_files_never_complete(self):
        with patch.object(sa, 'frozen_dataset', return_value={'dataset_fingerprint': 'gold'}), \
             patch.object(sa, 'app_fingerprint', return_value={'app_source_fingerprint': 'app'}), \
             patch.object(sa, 'questions', return_value=[]):
            status = sa.assess_completeness({}, 'baseline', Path('.'))
        self.assertFalse(status['complete'])
        self.assertEqual(len(status['issues']), len(sa.AGENTS))


if __name__ == '__main__':
    unittest.main()
