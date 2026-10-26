"""Validate each cached season as soon as all its weather responses exist."""
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

BASE=Path(__file__).resolve().parent
SEASONS=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2027)]
if __name__=='__main__':
    for season in SEASONS:
        raw=BASE/season/'raw'
        while len(list(raw.glob('*_weather.json.source.json')))<20:
            time.sleep(5)
        for command in [[sys.executable,str(BASE/'weather.py'),'build','--season',season],
                        [sys.executable,str(BASE/'verify_independently.py'),'--season',season]]:
            result=subprocess.run(command,capture_output=True,text=True)
            if result.returncode:
                print(result.stdout,result.stderr,flush=True)
                raise SystemExit(result.returncode)
        audit=json.loads((BASE/season/'verification.json').read_text())
        print(season,'verified:',audit['fixtures'],'fixtures;',audit['linked_rows'],
              'player links;',len(audit['hourly_sunshine_exceeds_daylight_fixtures']),'solar boundary flags.',flush=True)
