"""Verify included bytes and row universes; does not retrain the live model."""
from pathlib import Path
import csv,gzip,lzma,json,hashlib
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent

def check_rows(path,key,expected):
    opener=lzma.open if path.suffix=='.xz' else gzip.open if path.suffix=='.gz' else open
    seen=set();count=0
    with opener(path,'rt',newline='') as stream:
        for row in csv.DictReader(stream):
            item=tuple(row[c] for c in key)
            if item in seen:raise AssertionError(('Duplicate key',path,item))
            seen.add(item);count+=1
    assert count==expected,(path,count,expected)
    return count

def main():
    manifest=json.loads((P/'MANIFEST.json').read_text())
    for name,value in manifest['files'].items():
        p=R/name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==value['sha256'],name
    data=R/'datasets/fpl_component_common_20261026';schema=json.loads((data/'schema.json').read_text());active=json.loads((data/'active325_schema.json').read_text());assert len(schema['features'])==341 and len(active['features'])==325 and set(active['features'])<=set(schema['features'])
    tables=json.loads((data/'tables.json').read_text())
    for name,spec in tables.items():
        check_rows(data/spec['file'],['season','round','code'],spec['rows'])
        with lzma.open(data/spec['file'],'rt',newline='') as stream:columns=next(csv.reader(stream))
        assert set(schema['features'])<=set(columns)
    check_rows(R/'datasets/fpl_master_enriched_v5/player_matches.csv.xz',['season','fixture','code'],190124)
    check_rows(R/'datasets/fpl_live_observations_20261026/player_observations.csv.xz',['season','fixture','code'],4866)
    check_rows(R/'datasets/fpl_external_live_2026_10_26/player_minutes.csv.gz',['season','external_match_key','espn_player_id'],48598)
    assert json.loads((P/'EXPORT_VERIFICATION.json').read_text())['passed']
    print('Published files verified:',len(manifest['files']),'data row universes and selected325/341features passed')
if __name__=='__main__':main()
