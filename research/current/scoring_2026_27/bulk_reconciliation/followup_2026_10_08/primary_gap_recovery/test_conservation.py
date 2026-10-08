import unittest,math
from conservation import exhausts,cbi,legacy_net
class Conservation(unittest.TestCase):
 def test_missing_parent_is_not_zero(self):self.assertFalse(exhausts(math.nan,[None,math.nan]))
 def test_explicit_zero(self):self.assertTrue(exhausts(0,[None,math.nan,0]))
 def test_exact_positive_exhaustion(self):self.assertTrue(exhausts(3,[1,2,None]))
 def test_positive_residual(self):self.assertFalse(exhausts(4,[1,2,None]))
 def test_contradiction(self):self.assertFalse(exhausts(2,[1,2,None]))
 def test_invalid(self):self.assertFalse(exhausts(2,[1,-1,2]));self.assertFalse(exhausts(2,[.5,1.5]))
 def test_incomplete_cbi(self):self.assertIsNone(cbi([1,None,2]))
 def test_complete_cbi(self):self.assertEqual(cbi([1,0,2]),3)
 def test_signed_net(self):self.assertEqual(legacy_net(1,3),-1)
 def test_inconsistent_tackles(self):self.assertIsNone(legacy_net(3,2))
if __name__=='__main__':unittest.main()
