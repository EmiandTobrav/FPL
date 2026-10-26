"""All-season enriched observations, player role history and descriptive strength."""
import csv,hashlib,json,lzma
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent

def iter_records(view='observations',include_weather=None,before=None):
    if view not in ['observations','history']:raise ValueError('view must be observations or history')
    if include_weather is None:include_weather=view=='observations'
    if before is not None:
        before=datetime.fromisoformat(str(before).replace('Z','+00:00'))
        if before.tzinfo is None:raise ValueError('Timezone required')
    manifest=json.loads((HERE/'manifest.json').read_text())
    path=HERE/'player_matches.csv.xz'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['files']['player_matches.csv.xz']:
        raise ValueError('Master file hash mismatch')
    with lzma.open(path,'rt') as stream:
        for row in csv.DictReader(stream):
            if row['is_fpl_fixture']!='True' or row['competition']!='Premier League' or row['data_role']!='fpl_observation':
                raise ValueError('External competition row in FPL observation master')
            if view=='history' and row['history_eligible']!='True':continue
            if before is not None and datetime.fromisoformat(row['observation_available_after_proxy'])>=before:continue
            if not include_weather:row={k:v for k,v in row.items() if not k.startswith('weather_')}
            yield row

def load(view='observations',include_weather=None,before=None):
    """Return a pandas frame if pandas is available; iter_records needs only stdlib."""
    import pandas as pd
    return pd.DataFrame(iter_records(view,include_weather,before))
