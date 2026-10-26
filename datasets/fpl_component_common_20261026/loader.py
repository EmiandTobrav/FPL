"""Portable CSV exports; numerical types and missing values remain explicit."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent

def load_table(name='training'):
    import pandas as pd
    spec=json.loads((P/'tables.json').read_text())[name];path=P/spec['file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=spec['export_sha256']:raise ValueError('Changed exported table')
    objects={k:'object' for k,v in spec['dtypes'].items() if v=='object'}
    frame=pd.read_csv(path,dtype=objects,float_precision='round_trip',low_memory=False)
    for column,dtype in spec['dtypes'].items():
        if dtype.startswith('datetime64'):frame[column]=pd.to_datetime(frame[column],utc=True,format='mixed')
        elif dtype=='bool':
            values=frame[column].map({True:True,False:False,'True':True,'False':False})
            if values.isna().any():raise ValueError('Unknown Boolean value: '+column)
            frame[column]=values.astype(bool)
        elif dtype!='object':frame[column]=frame[column].astype(dtype)
    for column in spec.get('object_boolean_columns',[]):
        values=frame[column];restored=values.map({'True':True,'False':False,True:True,False:False})
        if (values.notna()&restored.isna()).any():raise ValueError('Unknown nullable Boolean: '+column)
        frame[column]=restored.astype(object)
    if len(frame)!=spec['rows'] or frame.duplicated(['season','round','code']).any():raise ValueError('Changed row universe')
    return frame
