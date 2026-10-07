import unittest
import pandas as pd
from recover import recover_team, name_match, team


def keeper(pid='keeper', explicit=None):
    return {'player_id':pid,'team_id':'defence','fpl_saves':5,
            'explicit_big_chance_saves':explicit}


def stats(shots=1, missed=1):
    return pd.DataFrame([dict(record_count=15,totalScoringAtt=shots,
                              bigChanceMissed=missed,bigChanceScored=0)])


def shot(eid=100, blocked=False, big=True, minute=50):
    return dict(event_id=eid,player_name='attacker',team_id='attack',
                minute=minute,second=0,type_id=15,big_chance=big,
                is_blocked=blocked,is_own_goal=False)


def event(eid, typ, pid, period=2, sec=0, q=None):
    q={} if q is None else q
    return dict(event_id=eid,type_id=typ,player_id=pid,player_name=pid,
                team_id='attack' if typ==15 else 'defence',minute=50,
                second=sec,period_id=period,q=q,qualifier_json=str(q))


class RecoveryTests(unittest.TestCase):
    def test_excludes_outfield_block(self):
        c,p,e=recover_team([keeper()],stats(2,2),pd.DataFrame([shot(),shot(101,True)]),pd.DataFrame())
        self.assertEqual(c,{'keeper':1});self.assertEqual(p,[])
        self.assertEqual(sum(x['blocked'] for x in e),1)

    def test_zero_requires_complete_shots(self):
        c,p,_=recover_team([keeper()],stats(1,0),pd.DataFrame([shot(big=False)]),pd.DataFrame())
        self.assertEqual(c['keeper'],0);self.assertEqual(p,[])
        _,p,_=recover_team([keeper()],stats(2,0),pd.DataFrame([shot(big=False)]),pd.DataFrame())
        self.assertIn('shot_count_mismatch',p)

    def test_missing_block_flag_is_not_zero(self):
        _,p,_=recover_team([keeper()],stats(),pd.DataFrame([shot(blocked=None)]),pd.DataFrame())
        self.assertIn('missing_block_flag',p)

    def test_missing_big_chance_flag_is_not_zero(self):
        _,p,_=recover_team([keeper()],stats(),pd.DataFrame([shot(big=None)]),pd.DataFrame())
        self.assertIn('missing_shot_flags',p)

    def test_period_prevents_wrong_keeper_at_same_clock(self):
        es=pd.DataFrame([event(100,15,'attacker',q={'214':None}),
                         event(200,10,'old',period=1),event(201,10,'new',period=2)])
        c,p,_=recover_team([keeper('old'),keeper('new')],stats(),pd.DataFrame([shot()]),es)
        self.assertEqual(c,{'old':0,'new':1});self.assertEqual(p,[])

    def test_rebound_sequence_with_same_keeper(self):
        es=pd.DataFrame([event(100,15,'attacker',q={'214':None}),
                         event(200,10,'new'),event(201,10,'new',sec=2)])
        c,p,_=recover_team([keeper('old'),keeper('new')],stats(),pd.DataFrame([shot()]),es)
        self.assertEqual(c['new'],1);self.assertEqual(p,[])

    def test_two_possible_keepers_stays_unresolved(self):
        es=pd.DataFrame([event(100,15,'attacker',q={'214':None}),
                         event(200,10,'old'),event(201,10,'new')])
        _,p,_=recover_team([keeper('old'),keeper('new')],stats(),pd.DataFrame([shot()]),es)
        self.assertIn('ambiguous_keeper_substitution',p)

    def test_conflicting_explicit_count_is_quarantined(self):
        _,p,_=recover_team([keeper(explicit=2)],stats(),pd.DataFrame([shot()]),pd.DataFrame())
        self.assertIn('explicit_count_conflict',p)

    def test_duplicate_shot_rejected(self):
        with self.assertRaises(ValueError):
            recover_team([keeper()],stats(2,2),pd.DataFrame([shot(),shot()]),pd.DataFrame())

    def test_identity_normalization(self):
        self.assertEqual(team('Brighton & Hove Albion FC'),team('Brighton'))
        self.assertEqual(name_match({'first_name':'Filip','second_name':'Jørgensen','web_name':'Jørgensen'},
                          {'first_name':'Filip','last_name':'Jörgensen','player_name':'F. Jörgensen'}),2)


if __name__=='__main__':unittest.main()
