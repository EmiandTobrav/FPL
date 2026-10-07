import hashlib
import json
from types import SimpleNamespace
import unittest

import pandas as pd
from build import KEY,P,S,adjudicate,clock_components,setup


def sample():
    target=SimpleNamespace(match_id='m',player_id='p0',team_id='home')
    q=json.dumps({'30':','.join(f'p{i}' for i in range(12)),
                  '44':','.join(['1']+['2']*10+['5']),
                  '131':','.join(map(str,list(range(1,12))+[0]))})
    rows=[]
    for typ,period,minute in [(32,1,0),(32,2,45),(30,1,47),(30,2,95),(34,16,0),(18,2,59),(19,2,59)]:
        rows.append(dict(match_id='m',event_id=len(rows),type_id=typ,period_id=period,minute=minute,
            second=40 if typ in [18,19] else 0,team_id='home',
            player_id='p0' if typ==18 else 'p11' if typ==19 else '',qualifier_json=q if typ==34 else '{}'))
    return target,pd.DataFrame(rows)


class ClockTests(unittest.TestCase):
    def test_distinct_rule_boundaries(self):
        self.assertEqual(clock_components(3599),(1,3))
        self.assertEqual(clock_components(3600),(2,3))
        self.assertEqual(clock_components(3601),(2,None))
        self.assertEqual(clock_components(3659),(2,None))
        self.assertEqual(clock_components(3660),(2,6))

    def test_zero_and_added_time_not_inferred(self):
        for value in [0,-1,5401]:
            with self.assertRaises(ValueError):clock_components(value)

    def test_starter_paired_exit_corroborates_fpl(self):
        t,e=sample();r=adjudicate(t,e,59)
        self.assertEqual(r['elapsed_regulation_seconds'],3580)
        self.assertTrue(r['scoring_requirement_discharged'])
        self.assertEqual((r['base_minute_points'],r['bps_minute_points']),(1,3))

    def test_no_blank_or_disagreeing_fpl_acceptance(self):
        t,e=sample()
        for fpl in [float('nan'),60]:
            self.assertEqual(adjudicate(t,e,fpl)['reason'],'clock_disagrees_with_completed_fpl_minutes')

    def test_must_have_starter_evidence(self):
        t,e=sample();e=e[e.type_id.ne(34)]
        self.assertEqual(adjudicate(t,e,59)['reason'],'missing_or_ambiguous_lineup')

    def test_corrupt_lineup_arrays_rejected(self):
        with self.assertRaises(ValueError):setup(json.dumps({'30':'a,b','44':'1','131':'1'}))

    def test_missing_period_anchor_rejected(self):
        t,e=sample();e=e[~(e.type_id.eq(32)&e.period_id.eq(2))]
        self.assertEqual(adjudicate(t,e,59)['reason'],'missing_period_anchor')

    def test_wrong_clock_reset_rejected(self):
        t,e=sample();e.loc[e.type_id.eq(32)&e.period_id.eq(2),'minute']=0
        self.assertEqual(adjudicate(t,e,59)['reason'],'unsupported_clock_convention')

    def test_unpaired_exit_rejected(self):
        t,e=sample();e=e[e.type_id.ne(19)]
        self.assertEqual(adjudicate(t,e,59)['reason'],'unbalanced_substitution_timestamp')

    def test_substitute_not_treated_as_starter(self):
        t,e=sample();t.player_id='p11'
        self.assertEqual(adjudicate(t,e,59)['reason'],'substitute_interval_requires_reconstruction')

    def test_dismissal_not_treated_as_normal_exit(self):
        t,e=sample();card=e.iloc[-2].copy();card['event_id']=100;card['type_id']=17;card['qualifier_json']='{"33":null}'
        e=pd.concat([e,pd.DataFrame([card])],ignore_index=True)
        self.assertEqual(adjudicate(t,e,59)['reason'],'dismissal_requires_separate_clock_review')

    def test_duplicate_event_rejected(self):
        t,e=sample();e=pd.concat([e,e.iloc[-1:]])
        self.assertEqual(adjudicate(t,e,59)['reason'],'duplicate_event_identity')

    def test_partial_bps_rule_abstention(self):
        t,e=sample();e.loc[e.type_id.isin([18,19]),'minute']=60
        r=adjudicate(t,e,60)
        self.assertFalse(r['scoring_requirement_discharged'])
        self.assertEqual(r['base_minute_points'],2)
        self.assertIsNone(r['bps_minute_points'])


class ArtifactTests(unittest.TestCase):
    def test_local_evidence_hashes(self):
        for path,sha in json.loads((P/'manifest.json').read_text())['inputs'].items():
            self.assertEqual(hashlib.sha256((S.parent/path).read_bytes()).hexdigest(),sha,path)

    def test_conservation_and_unique_counts(self):
        old=pd.read_csv(S/'official_revision/resolution_queue.csv.gz')
        new=pd.read_csv(P/'resolution_queue.csv.gz')
        d=pd.read_csv(P/'decisions.csv')
        self.assertEqual(len(d),710)
        self.assertFalse(d.duplicated(KEY).any())
        self.assertEqual(len(new),len(old))
        self.assertEqual(old.raw_stat_still_unresolved.sum(),new.raw_stat_still_unresolved.sum())
        gain=int(d.scoring_requirement_discharged.sum())
        self.assertEqual(new.scoring_requirement_discharged.sum()-old.scoring_requirement_discharged.sum(),gain)
        pending=new[~new.scoring_requirement_discharged]
        findings=json.loads((P/'findings.json').read_text())
        self.assertEqual(len(pending),findings['remaining_scoring_requirement_cells'])
        self.assertEqual(len(pending[KEY].drop_duplicates()),findings['remaining_unique_player_matches'])
        fields=pd.read_csv(P/'field_summary.csv')
        self.assertEqual(fields.remaining_scoring_cells.sum(),len(pending))
        self.assertEqual(fields[['missing_data','source_conflict','rule_unresolved']].sum().sum(),len(pending))

    def test_only_minute_components_changed(self):
        old=pd.read_csv(S/'official_revision/resolution_queue.csv.gz')
        new=pd.read_csv(P/'resolution_queue.csv.gz')
        pd.testing.assert_frame_equal(old[old.field.ne('minutes')].reset_index(drop=True),
                                      new[new.field.ne('minutes')][old.columns].reset_index(drop=True))
        patch=pd.read_csv(P/'minute_component_supplement.csv')
        self.assertTrue(patch.scoring_requirement_discharged.all())
        self.assertTrue(patch[['base_minute_points','bps_minute_points']].notna().all().all())
        self.assertTrue(patch.fpl_minutes.eq(patch.corroborated_completed_minutes).all())


if __name__=='__main__':unittest.main()
