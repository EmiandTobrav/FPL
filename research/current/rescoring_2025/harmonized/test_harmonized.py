import unittest
import pandas as pd
import numpy as np
from collect import parse
from build_labels import point_bounds,COUNTS
from repair import tests as prior_repair_tests
class TransformationTests(unittest.TestCase):
 def test_official_postponement_resolution(self):
  prior_repair_tests()
 def test_thresholds_and_unknowns(self):
  rows=[('DEF',90,[2,1,2,5,np.nan],2),('DEF',90,[2,1,2,4,20],0),('MID',90,[2,1,2,4,3],2),('FWD',90,[2,1,2,4,2],0),('MID',90,[2,1,2,4,np.nan],np.nan),('MID',90,[3,2,3,4,np.nan],2),('GK',90,[np.nan]*5,0),('MID',0,[np.nan]*5,0)]
  f=pd.DataFrame([dict(position=p,minutes=m,**dict(zip(COUNTS,c))) for p,m,c,_ in rows]);result,lo,hi,inferred=point_bounds(f)
  for i,(_,_,_,expected) in enumerate(rows):
   if pd.isna(expected):self.assertTrue(pd.isna(result[i]));self.assertEqual((lo[i],hi[i]),(0,2))
   else:self.assertEqual(result[i],expected)
  self.assertTrue(inferred[5]);self.assertFalse(inferred[0])
 def fixture(self):
  f=dict(match_id=1,date='2025-01-01',home='Arsenal',away='Chelsea',team_h_score=1,team_a_score=0,season='2024-25',id=7)
  g=dict(matchId=1,leagueId=47,finished=True,matchTimeUTCDate='2025-01-01T15:00:00Z',homeTeam=dict(id=10,name='Arsenal'),awayTeam=dict(id=20,name='Chelsea'))
  metrics={str(i):dict(key=k,stat=dict(value=v)) for i,(k,v) in enumerate([('minutes_played',90),('goals',0),('matchstats.headers.tackles',4),('tackles_won',2),('shot_blocks',1),('blocked_cross',3),('clearances',5),('interceptions',2),('recoveries',6)])}
  d=dict(general=g,header=dict(teams=[dict(score=1),dict(score=0)]),content=dict(playerStats={'42':dict(optaId='p123',teamId=10,name='Player',stats=[dict(stats=metrics)])}))
  return d,f
 def test_total_tackles_and_shot_blocks(self):
  d,f=self.fixture();row=parse(d,f)[0];self.assertEqual(row['code'],123);self.assertEqual(row['tackles'],4);self.assertEqual(row['blocks'],1);self.assertEqual(row['clearances'],5)
 def test_reject_wrong_match_identity(self):
  d,f=self.fixture();f['away']='Liverpool'
  with self.assertRaises(AssertionError):parse(d,f)
 def test_reject_wrong_side(self):
  d,f=self.fixture();d['content']['playerStats']['42']['teamId']=30
  with self.assertRaises(AssertionError):parse(d,f)
 def test_reject_duplicate_opta_code(self):
  d,f=self.fixture();d['content']['playerStats']['43']=d['content']['playerStats']['42'].copy()
  with self.assertRaises(AssertionError):parse(d,f)
if __name__=='__main__':unittest.main()
