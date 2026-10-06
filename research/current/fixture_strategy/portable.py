"""Readable decision archives; omit bulky hypothetical future plans explicitly."""
from pathlib import Path
import json,gzip,hashlib
HERE=Path(__file__).resolve().parent;OUT=HERE/'results';PORTABLE=HERE/'portable'
def main():
    PORTABLE.mkdir(exist_ok=True);manifest=[]
    for source in sorted(OUT.glob('trace_*.json.gz')):
        obj=json.loads(gzip.decompress(source.read_bytes()))
        for row in obj['trace']:row.pop('plan',None)
        target=PORTABLE/source.name.removesuffix('.gz')
        data=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode();target.write_bytes(data)
        manifest.append(dict(path=str(target.relative_to(HERE)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),source=str(source.relative_to(HERE)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),omitted_fields=['trace[*].plan']))
    (HERE/'portable_manifest.json').write_text(json.dumps(manifest,indent=2));print('Archived',len(manifest),'runs;',sum(x['bytes'] for x in manifest),'bytes')
if __name__=='__main__':main()
