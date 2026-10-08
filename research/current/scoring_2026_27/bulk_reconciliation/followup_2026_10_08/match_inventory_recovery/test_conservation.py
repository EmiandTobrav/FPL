import unittest
from predict import conserve
class ConservationTests(unittest.TestCase):
 def test_exact(self):self.assertTrue(conserve(5,[2,3]))
 def test_explicit_zero_empty(self):self.assertTrue(conserve(0,[]))
 def test_missing_not_zero(self):self.assertFalse(conserve(None,[]))
 def test_nan_not_zero(self):self.assertFalse(conserve(float('nan'),[]))
 def test_positive_residual(self):self.assertFalse(conserve(6,[2,3]))
 def test_negative_residual(self):self.assertFalse(conserve(4,[2,3]))
 def test_negative_total(self):
  with self.assertRaises(ValueError):conserve(-1,[])
 def test_negative_player(self):
  with self.assertRaises(ValueError):conserve(0,[1,-1])
 def test_fractional_total(self):
  with self.assertRaises(ValueError):conserve(1.5,[1])
 def test_fractional_player(self):
  with self.assertRaises(ValueError):conserve(1,[.5,.5])
if __name__=='__main__':unittest.main()
