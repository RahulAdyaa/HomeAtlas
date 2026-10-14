import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_eval import metrics,edit,overlap,has_terms
class MetricsTest(unittest.TestCase):
 def test_perfect(self):
  m=metrics(['a','b'],['a','b'],2);self.assertEqual(m['precision'],1);self.assertEqual(m['recall'],1);self.assertEqual(m['ndcg'],1);self.assertEqual(m['ap'],1)
 def test_missing_slots(self):self.assertEqual(metrics(['a'],['a'],10)['precision'],.1)
 def test_reciprocal_rank(self):self.assertEqual(metrics(['x','a'],['a'],3)['mrr'],.5)
 def test_no_answer(self):self.assertIsNone(metrics(['a'],[],5))
 def test_empty(self):self.assertEqual(metrics([],['a'],5)['recall'],0)
 def test_final_denominator(self):self.assertEqual(metrics(['a'],['a'])['precision'],1)
 def test_edit(self):self.assertEqual(edit('kitten','sitting'),3)
 def test_terms_boundaries(self):self.assertFalse(has_terms('18 months',['8']));self.assertTrue(has_terms('18 months',['18']))
 def test_multiset(self):self.assertEqual(overlap('a a b','a b'),2/3)
if __name__=='__main__':unittest.main()
