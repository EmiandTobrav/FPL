"""Field-by-field native comparison of the frozen, bounded source pilot."""
import decimal,gzip,importlib.util,json
import pandas as pd
from prepare import P,R,K,digest,save
from predict import SOURCE

def round_native(value):
    return decimal.Decimal(str(value)).quantize(decimal.Decimal('0.01'),rounding=decimal.ROUND_HALF_UP)
def main():
    for n,h in json.loads((P/'prediction_freeze.json').read_text()).items():assert digest(P/n)==h,n
    for n,h in json.loads((P/'dependencies.json').read_text()).items():assert digest(R/n)==h,n
    for n,h in json.loads((P/'source_files.json').read_text()).items():assert digest(R/n)==h,n
    # Reuse the already qualified date/club/score/side/native-code decoder.
    spec=importlib.util.spec_from_file_location('source_identity_decoder',SOURCE/'build.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    plan=pd.read_csv(SOURCE/'plan.csv');files=pd.read_csv(SOURCE/'inputs/source_manifest.csv').set_index(K[:2])
    for row in plan.to_dict('records'):
        raw=gzip.decompress((SOURCE/files.loc[(row['season'],row['fixture']),'path']).read_bytes());decoder.decode(row,raw)
    native=pd.read_csv(R/'training_dataset/scoring/results/historical_inventory.csv.xz',low_memory=False)
    corrected=pd.read_csv(R/'training_dataset/fpl_history_2022/reconciliation/expected_statistics_qualified.csv.xz',low_memory=False)
    reference=pd.concat([corrected[K+['expected_goals_qualified','expected_assists_qualified']].rename(columns=lambda n:n.removesuffix('_qualified')),native[native.season.eq('2023-24')][K+['expected_goals','expected_assists']]],ignore_index=True)
    reference=reference.melt(id_vars=K,value_vars=['expected_goals','expected_assists'],var_name='field',value_name='native_value');assert not reference.duplicated(K+['field']).any()
    pred=pd.read_csv(P/'predictions.csv.gz');controls=pred[pred.eligible].merge(reference,on=K+['field'],validate='one_to_one').dropna(subset=['native_value'])
    controls['source_rounded']=controls.value.map(round_native);controls['native_rounded']=controls.native_value.map(round_native);controls['agrees']=controls.source_rounded.eq(controls.native_rounded)
    out=P/'results';out.mkdir(exist_ok=True);save(controls,out/'native_comparisons.csv.gz');save(controls[~controls.agrees],out/'disagreements.csv.gz')
    gate=json.loads((P/'protocol.json').read_text())['gate'];reports=[]
    for field in ['expected_goals','expected_assists']:
        x=controls[controls.field.eq(field)];positive=int(x.native_value.gt(0).sum());fixtures=len(x[K[:2]].drop_duplicates());errors=int((~x.agrees).sum());qualified=len(x)>=gate['minimum_field_controls'] and positive>=gate['minimum_positive_native_controls'] and fixtures>=gate['minimum_reference_fixtures'] and errors==gate['maximum_disagreements']
        reports.append(dict(field=field,controls=len(x),positive_native_controls=positive,fixtures=fixtures,errors=errors,pilot_qualified=qualified,reference_seasons=sorted(x.season.unique())))
    report=dict(source_fixtures=len(plan),source_identity_decoder_sha256=digest(SOURCE/'build.py'),fields=reports,source_lineage_and_current_season_qualification_pending=True,canonical_modified=False,ledger_fields_closed=0,expected_fields_added=0,historical_deadline_availability_qualified=False)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));print(controls[~controls.agrees][K+['field','value','native_value']].head(8).to_string(index=False))
if __name__=='__main__':main()
