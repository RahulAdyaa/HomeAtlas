"""Independent arithmetic checks for retrieval metrics (no inference or fixtures)."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('retrieval_eval',Path(__file__).with_name('retrieval_eval.py'))
# Load only metric function AST: tests do not import model/network dependencies.
import ast, math
module=ast.parse(Path(__file__).with_name('retrieval_eval.py').read_text())
namespace={'math':math}
exec(compile(ast.Module(body=[next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='scores')],type_ignores=[]),'<metric-test>','exec'),namespace)
scores=namespace['scores']
class MetricChecks(unittest.TestCase):
    def test_known_ranked_example(self):
        m=scores(['x','a','b'],['a','b'],3)
        self.assertAlmostEqual(m['precision'],2/3);self.assertEqual(m['recall'],1)
        self.assertEqual(m['mrr'],.5);self.assertAlmostEqual(m['map'],(.5+2/3)/2)
        self.assertEqual(m['r_precision'],.5)
    def test_missing_slots_are_not_dropped(self):
        self.assertEqual(scores(['a'],['a'],10)['precision'],.1)
        self.assertEqual(scores([],['a'],5)['hit'],0)
    def test_unanswerable_is_not_zero_recall(self):
        self.assertIsNone(scores(['x'],[],5))
    def test_perfect_multi_relevant(self):
        m=scores(['a','b'],['a','b'],2)
        for value in m.values():self.assertEqual(value,1)
if __name__=='__main__':unittest.main()
